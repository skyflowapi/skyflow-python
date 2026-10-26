import base64
from types import SimpleNamespace

import pytest

from common.errors import SkyflowError
from common.utils.enums.detect import (
    DataSourceType,
    DeidentificationType,
    DetectRunStatus,
    EntityType,
    FileDataFormat,
    GuardrailsValidation,
)
from common.utils.enums.redaction_type import RedactionType
from common.vault.detect import (
    CheckGuardrailsRequest,
    DeidentifyFileRequest,
    DeidentifyStringRequest,
    DetectConfiguration,
    Detect,
    DetectController,
    Entity,
    GetRunRequest,
    PollOptions,
    RedactionLevel,
    ReidentifyFileRequest,
    ReidentifyStringRequest,
)
from common.vault.detect import _file_output_writer as writer
from common.vault.detect import _mappers as mappers
from common.vault.detect import _polling as polling
from common.vault.detect import _validations as validations

VAULT_ID = "vault123"
TOKEN = "bearer-token"


class _Raw:
    def __init__(self, data):
        self._data = data
        self.calls = []

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)

        def method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return SimpleNamespace(data=self._data, headers={})

        return method


class _FilesRaw:
    def __init__(self, run_id, run_data=None, reidentify_data=None):
        self.run_id = run_id
        self.run_data = list(run_data or [])
        self.reidentify_data = reidentify_data
        self.calls = []

    def deidentify_file_v2(self, **kwargs):
        self.calls.append(("deidentify_file_v2", (), kwargs))
        return SimpleNamespace(data=SimpleNamespace(run_id=self.run_id), headers={})

    def get_run_v2(self, run_id, **kwargs):
        self.calls.append(("get_run_v2", (run_id,), kwargs))
        return SimpleNamespace(data=self.run_data.pop(0), headers={})

    def reidentify_file_v2(self, **kwargs):
        self.calls.append(("reidentify_file_v2", (), kwargs))
        return SimpleNamespace(data=self.reidentify_data, headers={})


def _api(raw):
    return SimpleNamespace(with_raw_response=raw)


def _vault_client(strings=None, files=None, guardrails=None):
    return SimpleNamespace(
        get_logger=lambda: None,
        get_vault_id=lambda: VAULT_ID,
        get_current_bearer_token=lambda: TOKEN,
        get_sdk_metrics=lambda: {},
        initialize_client_configuration=lambda: None,
        get_strings_v2_api=lambda: _api(strings),
        get_files_v2_api=lambda: _api(files),
        get_guardrails_v2_api=lambda: _api(guardrails),
    )


def _metrics():
    return SimpleNamespace(size=1.5, word_count=10, character_count=53, slides=None, pages=2, duration=None)


def test_deidentify_string_maps_request_and_response():
    entity = SimpleNamespace(
        token="NAME_1", value="", entity_type="NAME",
        entity_scores={"NAME": 0.9152},
        location=SimpleNamespace(start_index=11, end_index=19, start_index_processed=11, end_index_processed=19),
    )
    data = SimpleNamespace(processed_text="My name is [NAME_1]", entities=[entity], metrics=_metrics())
    raw = _Raw(data)
    controller = DetectController(_vault_client(strings=raw))

    response = controller.deidentify_string(DeidentifyStringRequest(text="My name is John Doe", configuration_id="cfg"))

    name, args, kwargs = raw.calls[0]
    assert name == "deidentify_string_v2"
    assert kwargs["text"] == "My name is John Doe"
    assert kwargs["configuration_id"] == "cfg"
    assert "configuration" not in kwargs
    headers = kwargs["request_options"]["additional_headers"]
    assert headers["Authorization"] == "Bearer " + TOKEN
    assert "sky-metadata" in headers
    assert response.processed_text == "My name is [NAME_1]"
    assert response.entities[0].token == "NAME_1"
    assert response.entities[0].entity_type == "NAME"
    assert response.entities[0].location.start_index == 11
    assert response.metrics.character_count == 53


def test_deidentify_string_inline_config_injects_vault_id():
    raw = _Raw(SimpleNamespace(processed_text="x", entities=None, metrics=None))
    controller = DetectController(_vault_client(strings=raw))
    configuration = DetectConfiguration(detect=Detect(entities=[
        Entity(entity_type=EntityType.NAME, deidentification_type=DeidentificationType.VAULT_TOKEN, destination="persons.name"),
    ]))

    controller.deidentify_string(DeidentifyStringRequest(text="hi", configuration=configuration))

    _, _, kwargs = raw.calls[0]
    assert "configuration_id" not in kwargs
    wire = kwargs["configuration"].dict(by_alias=True, exclude_none=True)
    assert wire["vaultId"] == VAULT_ID
    assert wire["detect"]["entities"][0]["entityType"] == "NAME"
    assert wire["detect"]["entities"][0]["deidentificationType"] == "VAULT_TOKEN"


def test_reidentify_string_sends_vault_id():
    raw = _Raw(SimpleNamespace(processed_text="My name is John Doe", metrics=None))
    controller = DetectController(_vault_client(strings=raw))

    controller.reidentify_string(ReidentifyStringRequest(
        text="My name is [NAME_1]",
        redaction_level=[RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT)],
    ))

    _, _, kwargs = raw.calls[0]
    assert kwargs["vault_id"] == VAULT_ID
    assert kwargs["text"] == "My name is [NAME_1]"
    wire = [level.dict(by_alias=True, exclude_none=True) for level in kwargs["redaction_level"]]
    assert wire == [{"entityName": "NAME", "redactionType": "PLAIN_TEXT"}]


def test_deidentify_file_submit_only_status_none():
    files = _FilesRaw(run_id="run-1")
    controller = DetectController(_vault_client(files=files))

    response = controller.deidentify_file(DeidentifyFileRequest(
        data_source=DataSourceType.SKYFLOW_ID, value="sid", configuration_id="cfg",
    ))

    assert response.run_id == "run-1"
    assert response.status is None
    assert response.output == []
    assert [c[0] for c in files.calls] == ["deidentify_file_v2"]
    _, _, kwargs = files.calls[0]
    assert kwargs["data_source"] == "SKYFLOW_ID"
    assert kwargs["value"] == "sid"


def test_deidentify_file_polled_success_writes(tmp_path):
    input_file = tmp_path / "notes.pdf"
    input_file.write_bytes(b"input-bytes")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    run_data = [SimpleNamespace(
        status="SUCCESS", output_type="BASE64",
        output=[SimpleNamespace(
            processed_file=base64.b64encode(b"redacted").decode(), processed_file_type="REDACTED_FILE",
            processed_file_extension="pdf",
        )],
        metrics=_metrics(), message=None,
    )]
    files = _FilesRaw(run_id="run-2", run_data=run_data)
    controller = DetectController(_vault_client(files=files))

    response = controller.deidentify_file(DeidentifyFileRequest(
        file_path=str(input_file), configuration_id="cfg",
        poll_options=PollOptions(), output_directory=str(out_dir),
    ))

    submit = files.calls[0]
    assert submit[0] == "deidentify_file_v2"
    assert submit[2]["data_source"] == "BASE64"
    assert submit[2]["value"] == base64.b64encode(b"input-bytes").decode()
    assert submit[2]["data_format"] == "pdf"
    assert response.status == DetectRunStatus.SUCCESS
    assert response.run_id == "run-2"
    written = out_dir / "processed-notes.pdf"
    assert written.read_bytes() == b"redacted"


def test_get_run_trims_run_id_and_maps():
    data = SimpleNamespace(status="IN_PROGRESS", output_type=None, output=None, metrics=None, message=None)
    files = _FilesRaw(run_id="ignored", run_data=[data])
    controller = DetectController(_vault_client(files=files))

    response = controller.get_run(GetRunRequest(run_id="  run-9  "))

    assert files.calls[0][1][0] == "run-9"
    assert response.run_id == "run-9"
    assert response.status == DetectRunStatus.IN_PROGRESS
    assert response.output == []


def test_check_guardrails_maps():
    data = SimpleNamespace(text="prompt", validation="FAILED", toxic=True, denied_topic=False)
    raw = _Raw(data)
    controller = DetectController(_vault_client(guardrails=raw))

    response = controller.check_guardrails(CheckGuardrailsRequest(text="prompt", check_toxicity=True, deny_topics=["politics"]))

    _, _, kwargs = raw.calls[0]
    assert kwargs["vault_id"] == VAULT_ID
    assert kwargs["check_toxicity"] is True
    assert kwargs["deny_topics"] == ["politics"]
    assert response.validation == GuardrailsValidation.FAILED
    assert response.toxic is True


def test_reidentify_file_value_only():
    data = SimpleNamespace(status="SUCCESS", output_type="BASE64", output=[], metrics=None)
    files = _FilesRaw(run_id="n/a", reidentify_data=data)
    controller = DetectController(_vault_client(files=files))

    response = controller.reidentify_file(ReidentifyFileRequest(
        data_source=DataSourceType.BASE64, value="b64", data_format=FileDataFormat.TXT,
    ))

    _, _, kwargs = files.calls[0]
    assert kwargs["data_source"] == "BASE64"
    assert kwargs["value"] == "b64"
    assert kwargs["vault_id"] == VAULT_ID
    assert kwargs["data_format"] == "txt"
    assert response.status == DetectRunStatus.SUCCESS


def test_poll_run_backoff_and_budget():
    sleeps = []
    responses = [mappers.to_get_run_response("r", SimpleNamespace(
        status="QUEUED", output_type=None, output=None, metrics=None, message=None)) for _ in range(20)]

    def fetcher(run_id):
        return responses.pop(0)

    run = polling.poll_run("r", PollOptions(), fetcher, sleeper=sleeps.append)

    assert sleeps[:5] == [1, 2, 4, 8, 16]
    assert sum(sleeps) == 60
    assert run.status == DetectRunStatus.QUEUED


def test_poll_run_stops_on_terminal():
    calls = {"n": 0}

    def fetcher(run_id):
        calls["n"] += 1
        status = "SUCCESS" if calls["n"] == 2 else "IN_PROGRESS"
        return mappers.to_get_run_response("r", SimpleNamespace(
            status=status, output_type=None, output=None, metrics=None, message=None))

    sleeps = []
    run = polling.poll_run("r", PollOptions(), fetcher, sleeper=sleeps.append)

    assert calls["n"] == 2
    assert sleeps == [1]
    assert run.status == DetectRunStatus.SUCCESS


def test_poll_run_null_status_is_terminal_unknown():
    def fetcher(run_id):
        return None

    sleeps = []
    run = polling.poll_run("r", PollOptions(), fetcher, sleeper=sleeps.append)

    assert sleeps == []
    assert run.status == DetectRunStatus.UNKNOWN


def test_file_output_writer_names(tmp_path):
    outputs = [
        mappers.FileOutput(processed_file=base64.b64encode(b"a").decode(), processed_file_type="REDACTED_FILE", processed_file_extension=FileDataFormat.PDF),
        mappers.FileOutput(processed_file=base64.b64encode(b"b").decode(), processed_file_type="ENTITIES", processed_file_extension=None),
    ]
    written = writer.write_outputs(outputs, DataSourceType.BASE64, "invoice.pdf", str(tmp_path))
    names = sorted(p.rsplit("/", 1)[-1] for p in written)
    assert names == ["processed-entities-invoice.json", "processed-invoice.pdf"]


def test_file_output_writer_skips_presigned():
    outputs = [mappers.FileOutput(processed_file="http://x", processed_file_type="REDACTED_FILE", processed_file_extension=FileDataFormat.PDF)]
    assert writer.write_outputs(outputs, DataSourceType.PRESIGNED_URL, "a.pdf", None) == []


def test_validations():
    with pytest.raises(SkyflowError):
        validations.validate_deidentify_string_request(DeidentifyStringRequest(text="  "))
    with pytest.raises(SkyflowError):
        validations.validate_deidentify_file_request(DeidentifyFileRequest(data_source=DataSourceType.BASE64, value="x", file_path="y"))
    with pytest.raises(SkyflowError):
        validations.validate_deidentify_file_request(DeidentifyFileRequest(value="x", data_source=DataSourceType.BASE64, poll_options=None, output_directory="d"))
    with pytest.raises(SkyflowError):
        validations.validate_deidentify_file_request(DeidentifyFileRequest(value="x", data_source=DataSourceType.BASE64, poll_options=PollOptions(wait_time=301)))
    with pytest.raises(SkyflowError):
        validations.validate_reidentify_file_request(ReidentifyFileRequest(value="x"))
    with pytest.raises(SkyflowError):
        validations.validate_get_run_request(GetRunRequest(run_id=" "))
    validations.validate_deidentify_file_request(DeidentifyFileRequest(data_source=DataSourceType.BASE64, value="x"))

import base64
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace

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


class TestDetectController(unittest.TestCase):
    def test_deidentify_string_maps_request_and_response(self):
        entity = SimpleNamespace(
            token="NAME_1", value="", entity_type="NAME",
            entity_scores={"NAME": 0.9152},
            location=SimpleNamespace(start_index=11, end_index=19, start_index_processed=11, end_index_processed=19),
        )
        data = SimpleNamespace(processed_text="My name is [NAME_1]", entities=[entity], metrics=_metrics())
        raw = _Raw(data)
        controller = DetectController(_vault_client(strings=raw))

        response = controller.deidentify_string(DeidentifyStringRequest(text="My name is John Doe", configuration_id="cfg"))

        name, _args, kwargs = raw.calls[0]
        self.assertEqual(name, "deidentify_string_v2")
        self.assertEqual(kwargs["text"], "My name is John Doe")
        self.assertEqual(kwargs["configuration_id"], "cfg")
        self.assertNotIn("configuration", kwargs)
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers["Authorization"], "Bearer " + TOKEN)
        self.assertIn("sky-metadata", headers)
        self.assertEqual(response.processed_text, "My name is [NAME_1]")
        self.assertEqual(response.entities[0].token, "NAME_1")
        self.assertEqual(response.entities[0].entity_type, "NAME")
        self.assertEqual(response.entities[0].location.start_index, 11)
        self.assertEqual(response.metrics.character_count, 53)

    def test_deidentify_string_inline_config_injects_vault_id(self):
        raw = _Raw(SimpleNamespace(processed_text="x", entities=None, metrics=None))
        controller = DetectController(_vault_client(strings=raw))
        configuration = DetectConfiguration(detect=Detect(entities=[
            Entity(entity_type=EntityType.NAME, deidentification_type=DeidentificationType.VAULT_TOKEN, destination="persons.name"),
        ]))

        controller.deidentify_string(DeidentifyStringRequest(text="hi", configuration=configuration))

        _name, _args, kwargs = raw.calls[0]
        self.assertNotIn("configuration_id", kwargs)
        wire = kwargs["configuration"].dict(by_alias=True, exclude_none=True)
        self.assertEqual(wire["vaultId"], VAULT_ID)
        self.assertEqual(wire["detect"]["entities"][0]["entityType"], "NAME")
        self.assertEqual(wire["detect"]["entities"][0]["deidentificationType"], "VAULT_TOKEN")

    def test_reidentify_string_sends_vault_id(self):
        raw = _Raw(SimpleNamespace(processed_text="My name is John Doe", metrics=None))
        controller = DetectController(_vault_client(strings=raw))

        controller.reidentify_string(ReidentifyStringRequest(
            text="My name is [NAME_1]",
            redaction_level=[RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT)],
        ))

        _name, _args, kwargs = raw.calls[0]
        self.assertEqual(kwargs["vault_id"], VAULT_ID)
        self.assertEqual(kwargs["text"], "My name is [NAME_1]")
        wire = [level.dict(by_alias=True, exclude_none=True) for level in kwargs["redaction_level"]]
        self.assertEqual(wire, [{"entityName": "NAME", "redactionType": "PLAIN_TEXT"}])

    def test_deidentify_file_submit_only_status_none(self):
        files = _FilesRaw(run_id="run-1")
        controller = DetectController(_vault_client(files=files))

        response = controller.deidentify_file(DeidentifyFileRequest(
            data_source=DataSourceType.SKYFLOW_ID, value="sid", configuration_id="cfg",
        ))

        self.assertEqual(response.run_id, "run-1")
        self.assertIsNone(response.status)
        self.assertEqual(response.output, [])
        self.assertEqual([c[0] for c in files.calls], ["deidentify_file_v2"])
        _name, _args, kwargs = files.calls[0]
        self.assertEqual(kwargs["data_source"], "SKYFLOW_ID")
        self.assertEqual(kwargs["value"], "sid")

    def test_deidentify_file_polled_success_writes(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        input_file = os.path.join(tmp, "notes.pdf")
        with open(input_file, "wb") as handle:
            handle.write(b"input-bytes")
        out_dir = os.path.join(tmp, "out")
        os.makedirs(out_dir)
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
            file_path=input_file, configuration_id="cfg",
            poll_options=PollOptions(), output_directory=out_dir,
        ))

        submit = files.calls[0]
        self.assertEqual(submit[0], "deidentify_file_v2")
        self.assertEqual(submit[2]["data_source"], "BASE64")
        self.assertEqual(submit[2]["value"], base64.b64encode(b"input-bytes").decode())
        self.assertEqual(submit[2]["data_format"], "pdf")
        self.assertEqual(response.status, DetectRunStatus.SUCCESS)
        self.assertEqual(response.run_id, "run-2")
        with open(os.path.join(out_dir, "processed-notes.pdf"), "rb") as handle:
            self.assertEqual(handle.read(), b"redacted")

    def test_get_run_trims_run_id_and_maps(self):
        data = SimpleNamespace(status="IN_PROGRESS", output_type=None, output=None, metrics=None, message=None)
        files = _FilesRaw(run_id="ignored", run_data=[data])
        controller = DetectController(_vault_client(files=files))

        response = controller.get_run(GetRunRequest(run_id="  run-9  "))

        self.assertEqual(files.calls[0][1][0], "run-9")
        self.assertEqual(response.run_id, "run-9")
        self.assertEqual(response.status, DetectRunStatus.IN_PROGRESS)
        self.assertEqual(response.output, [])

    def test_check_guardrails_maps(self):
        data = SimpleNamespace(text="prompt", validation="FAILED", toxic=True, denied_topic=False)
        raw = _Raw(data)
        controller = DetectController(_vault_client(guardrails=raw))

        response = controller.check_guardrails(CheckGuardrailsRequest(text="prompt", check_toxicity=True, deny_topics=["politics"]))

        _name, _args, kwargs = raw.calls[0]
        self.assertEqual(kwargs["vault_id"], VAULT_ID)
        self.assertIs(kwargs["check_toxicity"], True)
        self.assertEqual(kwargs["deny_topics"], ["politics"])
        self.assertEqual(response.validation, GuardrailsValidation.FAILED)
        self.assertIs(response.toxic, True)

    def test_reidentify_file_value_only(self):
        data = SimpleNamespace(status="SUCCESS", output_type="BASE64", output=[], metrics=None)
        files = _FilesRaw(run_id="n/a", reidentify_data=data)
        controller = DetectController(_vault_client(files=files))

        response = controller.reidentify_file(ReidentifyFileRequest(
            data_source=DataSourceType.BASE64, value="b64", data_format=FileDataFormat.TXT,
        ))

        _name, _args, kwargs = files.calls[0]
        self.assertEqual(kwargs["data_source"], "BASE64")
        self.assertEqual(kwargs["value"], "b64")
        self.assertEqual(kwargs["vault_id"], VAULT_ID)
        self.assertEqual(kwargs["data_format"], "txt")
        self.assertEqual(response.status, DetectRunStatus.SUCCESS)

    def test_poll_run_backoff_and_budget(self):
        sleeps = []
        responses = [mappers.to_get_run_response("r", SimpleNamespace(
            status="QUEUED", output_type=None, output=None, metrics=None, message=None)) for _ in range(20)]

        def fetcher(_run_id):
            return responses.pop(0)

        run = polling.poll_run("r", PollOptions(), fetcher, sleeper=sleeps.append)

        self.assertEqual(sleeps[:5], [1, 2, 4, 8, 16])
        self.assertEqual(sum(sleeps), 60)
        self.assertEqual(run.status, DetectRunStatus.QUEUED)

    def test_poll_run_stops_on_terminal(self):
        calls = {"n": 0}

        def fetcher(_run_id):
            calls["n"] += 1
            status = "SUCCESS" if calls["n"] == 2 else "IN_PROGRESS"
            return mappers.to_get_run_response("r", SimpleNamespace(
                status=status, output_type=None, output=None, metrics=None, message=None))

        sleeps = []
        run = polling.poll_run("r", PollOptions(), fetcher, sleeper=sleeps.append)

        self.assertEqual(calls["n"], 2)
        self.assertEqual(sleeps, [1])
        self.assertEqual(run.status, DetectRunStatus.SUCCESS)

    def test_poll_run_null_status_is_terminal_unknown(self):
        def fetcher(_run_id):
            return None

        sleeps = []
        run = polling.poll_run("r", PollOptions(), fetcher, sleeper=sleeps.append)

        self.assertEqual(sleeps, [])
        self.assertEqual(run.status, DetectRunStatus.UNKNOWN)

    def test_file_output_writer_names(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        outputs = [
            mappers.FileOutput(processed_file=base64.b64encode(b"a").decode(), processed_file_type="REDACTED_FILE", processed_file_extension=FileDataFormat.PDF),
            mappers.FileOutput(processed_file=base64.b64encode(b"b").decode(), processed_file_type="ENTITIES", processed_file_extension=None),
        ]
        written = writer.write_outputs(outputs, DataSourceType.BASE64, "invoice.pdf", tmp)
        names = sorted(os.path.basename(path) for path in written)
        self.assertEqual(names, ["processed-entities-invoice.json", "processed-invoice.pdf"])

    def test_file_output_writer_skips_presigned(self):
        outputs = [mappers.FileOutput(processed_file="http://x", processed_file_type="REDACTED_FILE", processed_file_extension=FileDataFormat.PDF)]
        self.assertEqual(writer.write_outputs(outputs, DataSourceType.PRESIGNED_URL, "a.pdf", None), [])

    def test_validations(self):
        with self.assertRaises(SkyflowError):
            validations.validate_deidentify_string_request(DeidentifyStringRequest(text="  "))
        with self.assertRaises(SkyflowError):
            validations.validate_deidentify_file_request(DeidentifyFileRequest(data_source=DataSourceType.BASE64, value="x", file_path="y"))
        with self.assertRaises(SkyflowError):
            validations.validate_deidentify_file_request(DeidentifyFileRequest(value="x", data_source=DataSourceType.BASE64, poll_options=None, output_directory="d"))
        with self.assertRaises(SkyflowError):
            validations.validate_deidentify_file_request(DeidentifyFileRequest(value="x", data_source=DataSourceType.BASE64, poll_options=PollOptions(wait_time=301)))
        with self.assertRaises(SkyflowError):
            validations.validate_reidentify_file_request(ReidentifyFileRequest(value="x"))
        with self.assertRaises(SkyflowError):
            validations.validate_get_run_request(GetRunRequest(run_id=" "))
        validations.validate_deidentify_file_request(DeidentifyFileRequest(data_source=DataSourceType.BASE64, value="x"))


if __name__ == "__main__":
    unittest.main()

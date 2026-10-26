import base64

from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import ReidentifyFileRequest, RedactionLevel
from skyflow.utils.enums import DataSourceType, FileDataFormat, DetectRunStatus


def perform_reidentify_file():
    try:
        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',
            'cluster_id': '<YOUR_CLUSTER_ID>',
            'env': Env.PROD,
            'credentials': {'path': '<PATH_TO_YOUR_CREDENTIALS_JSON>'},
        }

        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        with open('<PATH_TO_TOKENIZED_FILE>', 'rb') as handle:
            encoded = base64.b64encode(handle.read()).decode('utf-8')

        request = ReidentifyFileRequest(
            data_source=DataSourceType.BASE64,
            value=encoded,
            data_format=FileDataFormat.TXT,
            redaction_level=[
                RedactionLevel(
                    token_group_name='<TOKEN_GROUP_NAME>',
                    redaction_pattern='<REDACTION_PATTERN>',
                ),
            ],
        )

        response = skyflow_client.detect().reidentify_file(request)

        print(response.status)
        if response.status == DetectRunStatus.SUCCESS:
            for index, output in enumerate(response.output):
                extension = output.processed_file_extension.value if output.processed_file_extension else 'txt'
                with open(f'reidentified-{index}.{extension}', 'wb') as out:
                    out.write(base64.b64decode(output.processed_file))

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })


if __name__ == '__main__':
    perform_reidentify_file()

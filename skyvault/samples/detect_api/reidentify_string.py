from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import ReidentifyStringRequest, RedactionLevel
from skyflow.utils.enums import EntityType, RedactionType


def perform_reidentify_string():
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

        request = ReidentifyStringRequest(
            text='My name is [NAME_1] and my email is [EMAIL_ADDRESS_1].',
            redaction_level=[
                RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT),
                RedactionLevel(entity_name=EntityType.EMAIL_ADDRESS, redaction_type=RedactionType.MASKED),
            ],
        )

        response = skyflow_client.detect().reidentify_string(request)

        print(response.processed_text)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })


if __name__ == '__main__':
    perform_reidentify_string()

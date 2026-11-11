from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import (
    DeidentifyStringRequest, DetectConfiguration, Detect, Entity,
    ReidentifyStringRequest, RedactionLevel,
)
from skyflow.utils.enums import EntityType, DeidentificationType


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

        deidentify_request = DeidentifyStringRequest(
            text='My name is John Doe, and my email is johndoe@acme.com.',
            configuration=DetectConfiguration(
                detect=Detect(
                    entities=[
                        Entity(
                            entity_type=EntityType.NAME,
                            deidentification_type=DeidentificationType.VAULT_TOKEN,
                            destination='<TOKEN_GROUP_NAME>',
                        ),
                    ],
                ),
            ),
        )

        deidentify_response = skyflow_client.detect().deidentify_string(deidentify_request)

        reidentify_request = ReidentifyStringRequest(
            text=deidentify_response.processed_text,
            redaction_level=[
                RedactionLevel(
                    token_group_name='<TOKEN_GROUP_NAME>',
                    redaction_pattern='<REDACTION_PATTERN>',
                ),
            ],
        )

        reidentify_response = skyflow_client.detect().reidentify_string(reidentify_request)

        print(reidentify_response.processed_text)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
            'request_id': error.request_id,
        })


if __name__ == '__main__':
    perform_reidentify_string()

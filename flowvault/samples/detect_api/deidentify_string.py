from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import DeidentifyStringRequest


def perform_deidentify_string():
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

        request = DeidentifyStringRequest(
            text='My name is John Doe, and my email is johndoe@acme.com.',
            configuration_id='<CONFIGURATION_ID>',
        )

        response = skyflow_client.detect().deidentify_string(request)

        print(response.processed_text)
        for entity in response.entities:
            print(entity.entity_type, entity.token, entity.entity_scores)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })


if __name__ == '__main__':
    perform_deidentify_string()

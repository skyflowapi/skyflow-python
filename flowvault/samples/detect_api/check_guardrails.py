from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import CheckGuardrailsRequest
from skyflow.utils.enums import GuardrailsValidation


def perform_check_guardrails():
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

        request = CheckGuardrailsRequest(
            text='<USER_PROMPT>',
            check_toxicity=True,
            deny_topics=['politics', 'medical advice'],
        )

        response = skyflow_client.detect().check_guardrails(request)

        if response.validation == GuardrailsValidation.FAILED:
            print('blocked', response.toxic, response.denied_topic)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
            'request_id': error.request_id,
        })


if __name__ == '__main__':
    perform_check_guardrails()

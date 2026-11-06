from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import GuardrailsValidation
from skyflow.vault.detect import CheckGuardrailsRequest

"""
 * Skyflow Check Guardrails Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Check text for toxicity and denied topics
 * 4. Handle response and errors
"""

def perform_check_guardrails():
    try:
        # Step 1: Configure Credentials
        credentials = {
            'path': '<PATH_TO_CREDENTIALS_JSON>'  # Path to your service account credentials file
        }

        # Step 2: Configure Vault
        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',  # Replace with your vault ID
            'cluster_id': '<YOUR_CLUSTER_ID>',  # Replace with your cluster ID
            'env': Env.PROD,  # Deployment environment
            'credentials': credentials
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        # Step 4: Create the request
        request = CheckGuardrailsRequest(
            text='<TEXT_TO_CHECK>',
            check_toxicity=True,  # Check the text for toxicity
            deny_topics=['politics', 'medical advice']  # Topics to deny
        )

        # Step 5: Check the text
        response = skyflow_client.detect(vault_config.get('vault_id')).check_guardrails(request)

        print('Validation:', response.validation, 'Toxic:', response.toxic, 'Denied topic:', response.denied_topic)
        if response.validation == GuardrailsValidation.FAILED:
            print('The text failed the guardrails check.')

    except SkyflowError as error:
        # Handle Skyflow-specific errors
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        # Handle unexpected errors
        print('Unexpected Error:', error)

# Invoke the check guardrails function
perform_check_guardrails()

from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import EntityType, DeidentificationType
from skyflow.vault.detect import DeidentifyStringRequest, DetectConfiguration, Detect, Entity

"""
 * Skyflow De-identify String Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. De-identify a string with a stored Detect configuration
 * 4. De-identify a string with an inline Detect configuration
 * 5. Handle response and errors
"""

def perform_deidentify_string():
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

        sample_text = 'My name is John Doe, and my email is johndoe@acme.com.'

        # Step 4: De-identify with the ID of an existing Detect configuration
        stored_config_request = DeidentifyStringRequest(
            text=sample_text,
            configuration_id='<CONFIGURATION_ID>'  # ID of an existing Detect configuration
        )

        response = skyflow_client.detect(vault_config.get('vault_id')).deidentify_string(stored_config_request)

        print('De-identified text:', response.processed_text)
        for entity in response.entities:
            print(entity.entity_type, entity.token, entity.entity_scores)

        # Step 5: De-identify with an inline Detect configuration
        inline_config_request = DeidentifyStringRequest(
            text=sample_text,
            configuration=DetectConfiguration(
                detect=Detect(entities=[
                    Entity(
                        entity_type=EntityType.NAME,
                        deidentification_type=DeidentificationType.VAULT_TOKEN,
                        destination='<TABLE_NAME>.<COLUMN_NAME>'  # Vault column that stores the detected value
                    ),
                    Entity(
                        entity_type=EntityType.EMAIL_ADDRESS,
                        deidentification_type=DeidentificationType.ENTITY_UNIQUE_COUNTER
                    )
                ])
            )
        )

        response = skyflow_client.detect(vault_config.get('vault_id')).deidentify_string(inline_config_request)

        print('De-identified text (inline configuration):', response.processed_text)

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

# Invoke the de-identify string function
perform_deidentify_string()

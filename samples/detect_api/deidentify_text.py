from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DetectEntities
from skyflow.vault.detect import DeidentifyTextRequest, TokenFormat, Transformations, DateTransformation

"""
 * Skyflow Text De-identification Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a deidentify text request with all available options
 * 4. Handle response and errors
"""

def perform_text_deidentification():
    try:
        # Step 1: Configure Credentials
        credentials = {
            'path': '/path/to/credentials.json'  # Path to credentials file
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

        # Step 4: Prepare Sample Text
        sample_text = "My SSN is 123-45-6789 and my card is 4111 1111 1111 1111."

        # Step 5: Configure Token Format
        token_format = TokenFormat(
            vault_token=[DetectEntities.CREDIT_CARD, DetectEntities.SSN],  # Use vault tokens for these entities
        )

        # Step 6: Configure Transformations
        transformations = Transformations(
            shift_dates=DateTransformation(
                max_days=30,  # Maximum days to shift
                min_days=30,  # Minimum days to shift
                entities=[DetectEntities.DOB]  # Apply shift to DOB entities
            )
        )

        # Step 7: Create Deidentify Request
        deidentify_request = DeidentifyTextRequest(
            text=sample_text,
            entities=[DetectEntities.CREDIT_CARD, DetectEntities.SSN],  # Entities to detect and deidentify
            token_format=token_format,
            transformations=transformations,
            allow_regex_list=['<YOUR_ALLOW_REGEX>'],  # Optional: regex patterns to allow
            restrict_regex_list=['<YOUR_RESTRICT_REGEX>']  # Optional: regex patterns to restrict
        )

        # Step 8: Perform Text Deidentification
        response = skyflow_client.detect().deidentify_text(deidentify_request)

        # Handle Successful Response
        print("\nDeidentify Text Response:", response)

    except SkyflowError as error:
        # Handle Skyflow-specific errors
        print('\nSkyflow Error:', {
            'http_code': error.http_code,
            'grpc_code': error.grpc_code,
            'http_status': error.http_status,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

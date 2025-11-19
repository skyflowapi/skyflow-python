from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DetectEntities, TokenType
from skyflow.vault.detect import DeidentifyTextRequest, TokenFormat

"""
 * Skyflow Detect with Vault Tokens Example
 * 
 * This example demonstrates how to use Vault Tokens when calling the Skyflow Detect endpoint
 * to deidentify text. Vault tokens provide a secure way to tokenize sensitive data.
 * 
 * This example shows:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a deidentify text request with Vault Token type
 * 4. Handle response and errors
"""

def perform_deidentify_with_vault_tokens():
    try:
        # Step 1: Configure Credentials
        # You can use any of the following authentication methods:
        # - API Key (Recommended)
        # - Service Account Credentials (file path or JSON string)
        # - Bearer Token
        # - Environment variable (SKYFLOW_CREDENTIALS)
        
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

        # Step 3: Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.INFO)  # Use LogLevel.ERROR in production
            .build()
        )

        # Example 1: Use VAULT_TOKEN as the default token type for all entities
        print("\n=== Example 1: Vault Token as Default ===")
        
        request = DeidentifyTextRequest(
            text="My SSN is 123-45-6789 and my credit card is 4111 1111 1111 1111",
            entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],
            token_format=TokenFormat(
                default=TokenType.VAULT_TOKEN  # Use vault tokens for all detected entities
            )
        )
        
        response = skyflow_client.detect('<YOUR_VAULT_ID>').deidentify_text(request)
        print('Response:', response)
        print('Processed Text:', response.processed_text)
        
        # Example 2: Use VAULT_TOKEN for specific entities only
        print("\n=== Example 2: Vault Token for Specific Entities ===")
        
        request = DeidentifyTextRequest(
            text="My SSN is 123-45-6789 and my credit card is 4111 1111 1111 1111",
            entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],
            token_format=TokenFormat(
                default=TokenType.ENTITY_ONLY,  # Default format for most entities
                vault_token=[DetectEntities.SSN]  # Use vault tokens only for SSN
            )
        )
        
        response = skyflow_client.detect('<YOUR_VAULT_ID>').deidentify_text(request)
        print('Response:', response)
        print('Processed Text:', response.processed_text)
        
        # Example 3: Mix different token types
        print("\n=== Example 3: Mixed Token Types ===")
        
        request = DeidentifyTextRequest(
            text="My name is John Doe, SSN is 123-45-6789, and card is 4111 1111 1111 1111",
            entities=[DetectEntities.NAME, DetectEntities.SSN, DetectEntities.CREDIT_CARD],
            token_format=TokenFormat(
                default=TokenType.ENTITY_ONLY,  # Default format
                vault_token=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],  # Vault tokens for SSN and card
                entity_unique_counter=[DetectEntities.NAME]  # Counter-based tokens for names
            )
        )
        
        response = skyflow_client.detect('<YOUR_VAULT_ID>').deidentify_text(request)
        print('Response:', response)
        print('Processed Text:', response.processed_text)
        
        # The entities field contains detailed information about each detected and tokenized entity
        if response.entities:
            print("\nDetected Entities:")
            for entity in response.entities:
                print(f"  - Entity: {entity.entity}")
                print(f"    Token: {entity.token}")
                print(f"    Original Value: {entity.value}")
                print(f"    Position in text: {entity.text_index}")

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
        # Handle unexpected errors
        print('Unexpected Error:', error)


if __name__ == '__main__':
    perform_deidentify_with_vault_tokens()

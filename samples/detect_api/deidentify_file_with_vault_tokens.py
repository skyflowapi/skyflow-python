from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DetectEntities, TokenType
from skyflow.vault.detect import DeidentifyFileRequest, FileInput, TokenFormat

"""
 * Skyflow Detect File with Vault Tokens Example
 * 
 * This example demonstrates how to use Vault Tokens when calling the Skyflow Detect endpoint
 * to deidentify files (text, documents, images, PDFs, etc.). Vault tokens provide a secure 
 * way to tokenize sensitive data found in files.
 * 
 * This example shows:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a deidentify file request with Vault Token type
 * 4. Handle response and errors
"""

def perform_deidentify_file_with_vault_tokens():
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

        # Step 3: Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.INFO)  # Use LogLevel.ERROR in production
            .build()
        )

        # Example 1: Deidentify a text file with vault tokens
        print("\n=== Example 1: Text File with Vault Tokens ===")
        
        with open('sensitive_document.txt', 'rb') as file:
            request = DeidentifyFileRequest(
                file=FileInput(file=file),
                entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],
                token_format=TokenFormat(
                    default=TokenType.VAULT_TOKEN  # Use vault tokens for all detected entities
                ),
                output_directory='/tmp/processed',  # Optional: Save processed file locally
                wait_time=30  # Maximum wait time in seconds for processing
            )
            
            response = skyflow_client.detect('<YOUR_VAULT_ID>').deidentify_file(request)
            print('Response Status:', response.status)
            print('Run ID:', response.run_id)
            print('File Type:', response.type)
            print('Extension:', response.extension)
            
            # The processed file is available as base64 string or as a file object
            if response.file:
                print('Processed file available')
                # You can read the file content
                content = response.file.read()
                print(f'File size: {len(content)} bytes')

        # Example 2: Deidentify with vault tokens for specific entities
        print("\n=== Example 2: Mixed Token Types ===")
        
        with open('document.txt', 'rb') as file:
            request = DeidentifyFileRequest(
                file=FileInput(file=file),
                entities=[DetectEntities.SSN, DetectEntities.NAME, DetectEntities.EMAIL],
                token_format=TokenFormat(
                    default=TokenType.ENTITY_ONLY,  # Default format
                    vault_token=[DetectEntities.SSN]  # Use vault tokens only for SSN
                ),
                wait_time=30
            )
            
            response = skyflow_client.detect('<YOUR_VAULT_ID>').deidentify_file(request)
            print('Response Status:', response.status)
            print('Entities found:', len(response.entities))
            
            # Access entity information
            if response.entities:
                print("\nEntity Information:")
                for entity_info in response.entities:
                    print(f"  Type: {entity_info.get('type')}")
                    print(f"  Extension: {entity_info.get('extension')}")

        # Example 3: Use file path instead of file object
        print("\n=== Example 3: Using File Path ===")
        
        request = DeidentifyFileRequest(
            file=FileInput(file_path='/path/to/sensitive_data.pdf'),
            entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD, DetectEntities.PHONE],
            token_format=TokenFormat(
                default=TokenType.VAULT_TOKEN
            ),
            wait_time=30
        )
        
        response = skyflow_client.detect('<YOUR_VAULT_ID>').deidentify_file(request)
        print('Response Status:', response.status)
        print('Run ID:', response.run_id)
        
        # Check processing metrics
        if response.word_count:
            print(f'Words processed: {response.word_count}')
        if response.char_count:
            print(f'Characters processed: {response.char_count}')
        if response.size_in_kb:
            print(f'File size: {response.size_in_kb} KB')

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
    perform_deidentify_file_with_vault_tokens()

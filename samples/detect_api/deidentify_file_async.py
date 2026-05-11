from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DetectEntities, MaskingMethod, DetectOutputTranscriptions
from skyflow.vault.detect import DeidentifyFileRequest, TokenFormat, Transformations, DateTransformation, Bleep, FileInput
from concurrent.futures import ThreadPoolExecutor

"""
 * Skyflow Deidentify File Example
 * 
 * This sample demonstrates how to use all available options for deidentifying files
 * using an asynchronous approach.
 * Supported file types: images (jpg, png, etc.), pdf, audio (mp3, wav), documents, 
 * spreadsheets, presentations, structured text.
"""

def perform_file_deidentification_async():
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
            .set_log_level(LogLevel.INFO)  # Use LogLevel.ERROR in production
            .build()
        )

        # Step 4: Create File Object
        file_path = '<FILE_PATH>'  # Replace with your file path
        
        deidentify_request = DeidentifyFileRequest(
            file=FileInput(file_path=file_path),  # File to de-identify
            # entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],  # Entities to detect
            allow_regex_list=['<YOUR_REGEX_PATTERN>'],  # Optional: Patterns to allow
            restrict_regex_list=['<YOUR_REGEX_PATTERN>'],  # Optional: Patterns to restrict

            # Token format configuration
            token_format=TokenFormat(
                vault_token=[DetectEntities.SSN],  # Use vault tokens for these entities
            ),

            # Optional: Custom transformations
            # transformations=Transformations(
            #     shift_dates=DateTransformation(
            #         max_days=30,
            #         min_days=10,
            #         entities=[DetectEntities.DOB]
            #     )
            # ),

                # Output configuration
                output_directory='<OUTPUT_DIRECTORY_PATH>',  # Where to save processed file
                wait_time=15,  # Max wait time in seconds (max 64)

            # Image-specific options
            output_processed_image=True,  # Include processed image in output
            output_ocr_text=True,  # Include OCR text in response
            masking_method=MaskingMethod.BLACKBOX,  # Masking method for images

            # PDF-specific options
            pixel_density=15,  # Pixel density for PDF processing
            max_resolution=2000,  # Max resolution for PDF

            # Audio-specific options
            output_processed_audio=True,  # Include processed audio
            output_transcription=DetectOutputTranscriptions.PLAINTEXT_TRANSCRIPTION,  # Transcription type

            # Audio bleep configuration

            # bleep=Bleep(
            #     gain=5,  # Loudness in dB
            #     frequency=1000,  # Pitch in Hz
            #     start_padding=0.1,  # Padding at start (seconds)
            #     stop_padding=0.2  # Padding at end (seconds)
            # )
        )
        
        # Create a thread pool executor
        executor = ThreadPoolExecutor(max_workers=1)
        
        future = executor.submit(
            lambda: skyflow_client.detect().deidentify_file(deidentify_request)
        )
        
        def handle_response(future):
            exception = future.exception()
            if exception is not None:
                if isinstance(exception, SkyflowError):
                    # Handle Skyflow-specific errors
                    print('\nSkyflow Error:', {
                        'http_code': exception.http_code,
                        'grpc_code': exception.grpc_code,
                        'http_status': exception.http_status,
                        'message': exception.message,
                        'details': exception.details
                    })
                else:
                    # Handle unexpected errors
                    print('Unexpected Error:', exception)
                return
            
            # Handle Successful Response
            result = future.result()
            print("\nDeidentify File Response:", result)
        
        future.add_done_callback(handle_response)

        executor.shutdown(wait=True)

    except Exception as error:
        # Handle unexpected errors
        print('Unexpected Error:', error)


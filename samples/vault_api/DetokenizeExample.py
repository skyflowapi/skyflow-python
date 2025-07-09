from skyflow import Skyflow, V1TokenGroupRedactions
import httpx


"""
Example demonstrating how to use the Skyflow Python SDK to detokenize values from a FlowDB vault.

Steps:
1. Set up the HTTP client with Bearer token authentication.
2. Create a Skyflow API client using the base URL and HTTP client.
3. Define the redaction settings for each token group.
4. Call the detokenize API with vault ID, tokens, and redaction config.
5. Handle and print the response.
"""

def perform_detokenization():
    try:
        # Step 1: Replace with your actual token and vault URL
        bearer_token = "<BEARER_TOKEN>"
        base_url = "<VAULT_URL>"

        # Step 2: Create a custom HTTPX client with Bearer token in headers
        httpx_client = httpx.Client(
            headers={
                "Authorization": f"Bearer {bearer_token}"
            }
        )

        # Step 3: Initialize the Skyflow client with the custom HTTP client
        client = Skyflow(
            base_url=base_url,
            httpx_client=httpx_client
        )

        # Step 4: Define redaction settings per token group
        redactions = [
            V1TokenGroupRedactions(
                token_group_name="<TOKEN_GROUP_NAME_1>",
                redaction="plain_text"
            ),
            V1TokenGroupRedactions(
                token_group_name="<TOKEN_GROUP_NAME_2>",
                redaction="plain_text"
            )
        ]

        # Step 5: Call the detokenize API
        response = client.flowservice.detokenize(
            vault_id="<VAULT_ID>",
            tokens=["<TOKEN_1>", "<TOKEN_2>"],
            token_group_redactions=redactions
        )

        # Step 6: Print the detokenize response
        print("Detokenize Response:")
        print(response)

    except Exception as e:
        print("Error occurred during detokenization:")
        print(e)

# Invoke the detokenization function
perform_detokenization()
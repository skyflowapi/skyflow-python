from src.skyflow import Skyflow
import httpx

"""
Example demonstrating how to use the Skyflow Python SDK to delete records from a VaultLH vault using Skyflow IDs.

Steps:
1. Set up the HTTP client with Bearer token authentication.
2. Create a Skyflow API client using the base URL and HTTP client.
3. Call the delete API with vault ID and Skyflow IDs.
4. Handle and print the response.
"""

def perform_record_deletion():
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

        # Step 3: Initialize the Skyflow client
        client = Skyflow(
            base_url=base_url,
            httpx_client=httpx_client
        )

        # Step 4: Perform the delete operation with one or more Skyflow IDs
        response = client.flowservice.delete(
            vault_id="<VAULT_ID>",
            skyflow_i_ds=["<SKYFLOW_ID_1>", "<SKYFLOW_ID_2>"]
        )

        # Step 5: Print the delete response
        print("Delete Response:")
        print(response)

    except Exception as e:
        print("Error occurred during delete operation:")
        print(e)


# Run the example
perform_record_deletion()

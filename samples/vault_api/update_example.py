from src.skyflow import Skyflow, V1UpdateRecordData
import httpx

"""
Example demonstrating how to use the Skyflow Python SDK to update records in a VaultLH vault.

Steps:
1. Set up the HTTP client with Bearer token authentication.
2. Create a Skyflow API client using the base URL and HTTP client.
3. Prepare the record data with Skyflow ID and updated values.
4. Call the update API with vault ID, table name, and updated records.
5. Handle and print the response.
"""


def perform_update():
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

        # Step 4: Prepare the update record with Skyflow ID and new values
        record = V1UpdateRecordData(
            skyflow_id="<SKYFLOW_ID>",
            data={
                "<COLUMN_NAME>": "<COLUMN_VALUE>",
            },
            tokens={
                "<COLUMN_NAME>": "<TOKEN_VALUE>",
            }
        )

        # Step 5: Perform the update operation
        response = client.flowservice.update(
            vault_id="<VAULT_ID>",
            table_name="<TABLE_NAME>",
            records=[record]
        )

        # Step 6: Print the update response
        print("Update Response:")
        print(response)

    except Exception as e:
        print("Error occurred during update operation:")
        print(e)


# Invoke the update function
perform_update()

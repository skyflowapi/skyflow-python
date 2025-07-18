from skyflow import Skyflow, V1ColumnRedactions
import httpx

"""
Example demonstrating how to use the Skyflow Python SDK to retrieve records from a VaultLH vault.

Steps:
1. Set up the HTTP client with Bearer token authentication.
2. Create a Skyflow API client using the base URL and HTTP client.
3. Fetch records either by Skyflow IDs or by column values with redaction settings.
4. Call the get API with appropriate parameters for each case.
5. Handle and print the response.
"""
def get_records_by_ids():
    try:
        # Step 1: Replace with your actual token and vault URL
        bearer_token = "<BEARER_TOKEN>"
        base_url = "<VAULT_URL>"

        # Step 2: Create HTTPX client with Bearer token
        httpx_client = httpx.Client(
            headers={"Authorization": f"Bearer {bearer_token}"}
        )

        # Step 3: Initialize the Skyflow client
        client = Skyflow(
            base_url=base_url,
            httpx_client=httpx_client
        )

        # Step 4: Call get API with Skyflow IDs
        response = client.flowservice.get(
            vault_id="<VAULT_ID>",
            table_name="<TABLE_NAME>",
            skyflow_ids=["<SKYFLOW_ID_1>", "<SKYFLOW_ID_2>"]
        )

        # Step 5: Print the response
        print("Get Records by Skyflow IDs Response:")
        print(response)

    except Exception as e:
        print("Error occurred during get by Skyflow IDs:")
        print(e)


def get_records_by_column_values():
    try:
        # Step 1: Replace with your actual token and vault URL
        bearer_token = "<BEARER_TOKEN>"
        base_url = "<VAULT_URL>"

        # Step 2: Create HTTPX client with Bearer token
        httpx_client = httpx.Client(
            headers={"Authorization": f"Bearer {bearer_token}"}
        )

        # Step 3: Initialize the Skyflow client
        client = Skyflow(
            base_url=base_url,
            httpx_client=httpx_client
        )

        # Step 4: Define redactions for specific columns
        redactions = [
            V1ColumnRedactions(column_name="name", redaction="plain_text"),
            V1ColumnRedactions(column_name="email", redaction="plain_text")
        ]

        # Step 5: Call get API with column values
        response = client.flowservice.get(
            vault_id="<VAULT_ID>",
            table_name="<TABLE_NAME>",
            columns=["name", "email"],
            column_redactions=redactions,
            limit=1
        )

        # Step 6: Print the response
        print("Get Records by Column Values Response:")
        print(response)

    except Exception as e:
        print("Error occurred during get by column values:")
        print(e)


# Call both functions
get_records_by_ids()
get_records_by_column_values()
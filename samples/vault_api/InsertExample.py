from skyflow import Skyflow, V1InsertRecordData
import httpx

"""
Example demonstrating how to use the Skyflow Python SDK to insert records into a FlowDB vault.

Steps:
1. Set up the HTTP client with Bearer token authentication.
2. Create a Skyflow API client using the base URL and HTTP client.
3. Prepare the record data to be inserted.
4. Call the insert API with vault ID, table name, and records.
5. Handle and print the response.
"""
def perform_secure_data_insertion():
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

        # Step 4: Prepare record data for insertion
        record_data = {
            "<COLUMN_NAME_1>": "<COLUMN_VALUE_1>",
            "<COLUMN_NAME_2>": "<COLUMN_VALUE_2>"
        }
        record = V1InsertRecordData(data=record_data)

        # Step 5: Perform the insert operation
        response = client.flowservice.insert(
            vault_id="<VAULT_ID>",
            table_name="<TABLE_NAME>",
            records=[record]
        )

        # Step 6: Print the insert response
        print("Insert Response:")
        print(response)

    except Exception as e:
        print("Error occurred during insert operation:")
        print(e)


# Invoke the secure data insertion function
perform_secure_data_insertion()
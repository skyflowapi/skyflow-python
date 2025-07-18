from src.skyflow import Skyflow, V1InsertRecordData, V1Upsert, FlowEnumUpdateType
import httpx

"""
Example demonstrating how to use the Skyflow Python SDK to insert records into a VaultLH vault with upsert support.

Steps:
1. Set up the HTTP client with Bearer token authentication.
2. Create a Skyflow API client using the base URL and HTTP client.
3. Prepare the record data to be inserted.
4. Specify upsert configuration (update if record exists).
5. Call the insert API with vault ID, table name, records, and upsert option.
6. Handle and print the response.
"""

def perform_secure_data_insertion():
    try:
        # Step 1: Replace with your actual Bearer token and vault URL
        bearer_token = "<BEARER_TOKEN>"
        base_url = "<VAULT_URL>"

        # Step 2: Create an HTTPX client with the Bearer token
        httpx_client = httpx.Client(
            headers={
                "Authorization": f"Bearer {bearer_token}"
            }
        )

        # Step 3: Instantiate the Skyflow client
        client = Skyflow(
            base_url=base_url,
            httpx_client=httpx_client
        )

        # Step 4: Prepare record for insertion
        record_data = {
            "<COLUMN_NAME>": "<COLUMN_VALUE>",
            "<COLUMN_NAME>": "<COLUMN_VALUE>",
        }
        record = V1InsertRecordData(data=record_data)

        # Step 5: Configure upsert behavior - update if email matches
        upsert_options = V1Upsert(
            update_type="UPDATE",
            unique_columns=["email"]
        )

        # Step 6: Perform insert with upsert
        response = client.flowservice.insert(
            vault_id="<VAULT_ID>",
            table_name="<TABLE_NAME>",
            records=[record],
            upsert=upsert_options
        )

        # Step 7: Output the response
        print("Insert (Upsert) Response:")
        print(response)

    except Exception as e:
        print("Error occurred during insert operation:")
        print(e)


# Run the example
perform_secure_data_insertion()
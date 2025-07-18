from skyflow import Skyflow
import httpx

"""
Example demonstrating how to use the Skyflow Python SDK to query records from a VaultLH vault.

Steps:
1. Set up the HTTP client with Bearer token authentication.
2. Create a Skyflow API client using the base URL and HTTP client.
3. Define the SQL-style query string.
4. Call the query API with vault ID and the query string.
5. Handle and print the response.
"""

def perform_record_query():
    try:
        # Step 1: Replace with your actual Bearer token and vault URL
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

        # Step 4: Define the query string (SQL-like syntax supported by Skyflow)
        query_string = "SELECT name, email FROM table1 LIMIT 10"

        # Step 5: Perform the query operation
        response = client.flowservice.executequery(
            vault_id="<VAULT_ID>",
            query=query_string
        )

        # Step 6: Print the query response
        print("Query Response:")
        print(response)

    except Exception as e:
        print("Error occurred during query operation:")
        print(e)


# Run the example
perform_record_query()

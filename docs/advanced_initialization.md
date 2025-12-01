# Advanced Skyflow Client Initialization

This guide demonstrates advanced initialization patterns for the Skyflow Python SDK, including multiple vault configurations and different credential types.

Use multiple vault configurations when your application needs to access data across different Skyflow vaults, such as managing data across different geographic regions or distinct environments.

To get started, you must first initialize the skyflow client. While initializing the skyflow client, you can specify different types of credentials.  
**1. API keys**  
- A unique identifier used to authenticate and authorize requests to an API.  

**2. Bearer tokens**  
- A temporary access token used to authenticate API requests, typically included in the
Authorization header.  

**3. Service account credentials file path**  
- The file path pointing to a JSON file containing credentials for a service account, used
for secure API access.  

**4. Service account credentials string**  
- A JSON-formatted string containing service account credentials, often used as an alternative to a file for programmatic authentication.  

Note: Only one type of credential can be used at a time.

```python
import json
from skyflow import Skyflow
from skyflow import LogLevel
from skyflow import Env

"""
Example program to initialize the Skyflow client with various configurations.
The Skyflow client facilitates secure interactions with the Skyflow vault, 
such as securely managing sensitive data.
"""

# Step 1: Define the primary credentials for authentication.
# Note: Only one type of credential can be used at a time. You can choose between:
# - API key
# - Bearer token
# - A credentials string (JSON-formatted)
# - A file path to a credentials file.

# Initialize primary credentials using a Bearer token for authentication.
primary_credentials = {
    'token': '<BEARER_TOKEN>'  # Replace <BEARER_TOKEN> with your actual authentication token.
}

# Step 2: Configure the primary vault details.
# VaultConfig stores all necessary details to connect to a specific Skyflow vault.
primary_vault_config = {
    'vault_id': '<PRIMARY_VAULT_ID>',  # Replace with your primary vault's ID.
    'cluster_id': '<CLUSTER_ID>',      # Replace with the cluster ID (part of the vault URL, e.g., https://{clusterId}.vault.skyflowapis.com).
    'env': Env.PROD,                    # Set the environment (PROD, SANDBOX, STAGE, DEV).
    'credentials': primary_credentials  # Attach the primary credentials to this vault configuration.
}

# Step 3: Create credentials as a JSON object (if a Bearer Token is not provided).
# Demonstrates an alternate approach to authenticate with Skyflow using a credentials object.
skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',       # Replace with your Client ID.
    'clientName': '<YOUR_CLIENT_NAME>',   # Replace with your Client Name.
    'tokenURI': '<YOUR_TOKEN_URI>',       # Replace with the Token URI.
    'keyID': '<YOUR_KEY_ID>',             # Replace with your Key ID.
    'privateKey': '<YOUR_PRIVATE_KEY>'    # Replace with your Private Key.
}

# Step 4: Convert the JSON object to a string and use it as credentials.
# This approach allows the use of dynamically generated or pre-configured credentials.
credentials_string = json.dumps(skyflow_credentials)  # Converts JSON object to string for use as credentials.

# Step 5: Define secondary credentials (API key-based authentication as an example).
# Demonstrates a different type of authentication mechanism for Skyflow vaults.
secondary_credentials = {
    'api_key': '<API_KEY>'  # Replace with your API Key for authentication.
}

# Step 6: Configure the secondary vault details.
# A secondary vault configuration can be used for operations involving multiple vaults.
secondary_vault_config = {
    'vault_id': '<SECONDARY_VAULT_ID>',  # Replace with your secondary vault's ID.
    'cluster_id': '<CLUSTER_ID>',        # Replace with the corresponding cluster ID.
    'env': Env.PROD,                      # Set the environment for this vault.
    'credentials': secondary_credentials  # Attach the secondary credentials to this configuration.
}

# Step 7: Define tertiary credentials using a path to a credentials JSON file.
# This method demonstrates an alternative authentication method.
tertiary_credentials = {
    'path': '<YOUR_CREDENTIALS_FILE_PATH>'  # Replace with the path to your credentials file.
}

# Step 8: Configure the tertiary vault details.
tertiary_vault_config = {
    'vault_id': '<TERTIARY_VAULT_ID>',   # Replace with the tertiary vault ID.
    'cluster_id': '<CLUSTER_ID>',        # Replace with the corresponding cluster ID.
    'env': Env.PROD,                      # Set the environment for this vault.
    'credentials': tertiary_credentials  # Attach the tertiary credentials.
}

# Step 9: Build and initialize the Skyflow client.
# Skyflow client is configured with multiple vaults and credentials.
skyflow_client = (
    Skyflow.builder()
    .add_vault_config(primary_vault_config)   # Add the primary vault configuration.
    .add_vault_config(secondary_vault_config) # Add the secondary vault configuration.
    .add_vault_config(tertiary_vault_config)  # Add the tertiary vault configuration.
    .add_skyflow_credentials(skyflow_credentials)  # Add JSON-formatted credentials if applicable.
    .set_log_level(LogLevel.ERROR)  # Set log level for debugging or monitoring purposes.
    .build()
)

# The Skyflow client is now fully initialized.
# Use the `skyflow_client` object to perform secure operations such as:
# - Inserting data
# - Retrieving data
# - Deleting data
# within the configured Skyflow vaults.

```
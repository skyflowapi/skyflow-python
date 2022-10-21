# Python SDK samples
Test the SDK by adding `VAULT-ID`, `VAULT-URL`, and `SERVICE-ACCOUNT` details in the required places for each sample.

## Prerequisites
-  A Skyflow account. If you don't have one, register for one on the [Try Skyflow](https://skyflow.com/try-skyflow) page.
- Python 3.7.0 or higher.

## Prepare
- Install the Python SDK:

        pip install skyflow

### Create the vault
1. In a browser, sign in to Skyflow Studio.
2. Create a vault by clicking **Create Vault** > **Start With a Template** > **Quickstart vault**.
3. Once the vault is ready, click the gear icon and select **Edit Vault Details**.
4. Note your **Vault URL** and **Vault ID** values, then click **Cancel**. You'll need these later.

### Create a service account
1. In the side navigation click, **IAM** > **Service Accounts** > **New Service Account**.
2. For **Name**, enter "SDK Sample". For **Roles**, choose **Vault Editor**.
3. Click **Create**. Your browser downloads a **credentials.json** file. Keep this file secure, as You'll need it for each of the samples.

## The samples
### Detokenize
Detokenize a data token from the vault. Make sure the specified token is for data that exists in the vault. If you need a valid token, use [insert_sample.py](insert_sample.py) to insert the data, then use this data's token for detokenization.
#### Configure
1. Replace **<YOUR_VAULT_ID>** with **VAULT ID**
2. Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
3. Replace **<FIELD_NAME>** with **COLUMN NAME**.
4. Replace **<TOKEN>** with **Data Token**.
5. Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
#### Run the sample

    python3 detokenize_sample.py

### GetById
Get data using skyflow id. 
#### Configure
1. Replace **<YOUR_VAULT_ID>** with **VAULT ID**
2. Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
3. Replace **<SKYFLOW_ID1>** with **Skyflow Id 1**.
4. Replace **<SKYFLOW_ID2>** with **Skyflow Id 2**.
5. Replace **<SKYFLOW_ID3>** with **Skyflow Id 3**.
6. Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
7. Replace **<TABLE_NAME>** with **credit_cards**.
 #### Run the sample
            
    python3 get_by_ids_sample.py

### Insert
Insert data in the vault.
#### Configure
1. Replace **<YOUR_VAULT_ID>** with **VAULT ID**.
2. Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
3. Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
4. Replace **<TABLE_NAME>** with **credit_cards**.
5. Replace **<FIELD_NAME>** with **column name**.
6. Replace **<VALUE>** with **valid value corresponding to column name**.
#### Run the sample
    
    python3 insert_sample.py
### InvokeConnection
Skyflow Connections is a gateway service that uses Skyflow's underlying tokenization capabilities to securely connect to first-party and third-party services. This way, your infrastructure is never directly exposed to sensitive data, and you offload security and compliance requirements to Skyflow.
#### Configure
1. Replace **<YOUR_VAULT_ID>** with **VAULT ID**.
2. Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
3. Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
4. Replace **<YOUR_CONNECTION_URL>** with **Connection url**.
5. Replace **<YOUR_CONNECTION_BASIC_AUTH>** with **access token**.
6. Replace value of **requestBody** with your's request body content.
7. Replace value of **pathParams** with your's path params content.
#### Run the sample
    
    python3 invoke_connection_sample.py
    
### Service account token generation
Generates SA Token using path of credentials file.
#### Configure
1. Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.

#### Run the sample
    
    python3 sa_token_sample.py

### Generate Bearer Token From Credentails
Generates SA Token using json content of credentials file.
#### Configure
1. Replace **credentials** with json data of downloaded credentials file while creation Service account.

#### Run the sample
    
    python3 generate_bearer_token_from_creds_sample.py
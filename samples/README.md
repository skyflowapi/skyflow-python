# PYTHON-SDK sample templates
Use this folder to test the functionalities of PYTHON-SDK just by adding `VAULT-ID` `VAULT-URL` and `SERVICE-ACCOUNT` details at the required place.

## Prerequisites
- A Skylow account. If you don't have one, you can register for one on the [Try Skyflow](https://skyflow.com/try-skyflow) page.
- Python 3.7.0 and above.

## Configure
- Before you can run the sample app, create a vault
- The package can be installed using pip:

        pip install skyflow

### Create the vault
1. In a browser, navigate to Skyflow Studio and log in.
2. Create a vault by clicking **Create Vault** > **Start With a Template** > **Quickstart vault**.
3. Once the vault is created, click the gear icon and select **Edit Vault** Details.
4. Note your Vault URL and Vault ID values, then click Cancel. You'll need these later.

### Create a service account
1. In the side navigation click, **IAM** > **Service Accounts** > **New Service Account**.
2. For Name, enter **Test-Python-Sdk-Sample**. For Roles, choose the required roles for specific action.
3. Click **Create**. Your browser downloads a **credentials.json** file. Keep this file secure, as you'll need it in the next steps.

### Different types of functionalities of Java-Sdk
- [**Detokenize**](detokenize_sample.py)
    - Detokenize the data token from the vault. 
    - Make sure the token is of the data which exists in the Vault. If not so please make use of [insert_sample.py](insert_sample.py) to insert the data in the data and use this token for detokenization.
    - Configure
        - Replace **<YOUR_VAULT_ID>** with **VAULT ID**
        - Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
        - Replace **<FIELD_NAME>** with **COLUMN NAME**.
        - Replace **<TOKEN>** with **Data Token**.
        - Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
    - Execution
        
            python3 detokenize_smaple.py
- [**GetById**](get_by_ids_sample.py)
    - Get data using skyflow id. 
    - Configure
        - Replace **<YOUR_VAULT_ID>** with **VAULT ID**
        - Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
        - Replace **<SKYFLOW_ID1>** with **Skyflow Id 1**.
        - Replace **<SKYFLOW_ID2>** with **Skyflow Id 2**.
        - Replace **<SKYFLOW_ID3>** with **Skyflow Id 3**.
        - Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
        - Replace **<TABLE_NAME>** with **credit_cards**.
    - Execution
            
            python3 get_by_ids_sample.py
- [**Insert**](insert_sample.py)
    - Insert data in the vault.
    - Configure
        - Replace **<YOUR_VAULT_ID>** with **VAULT ID**.
        - Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
        - Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
        - Replace **<TABLE_NAME>** with **credit_cards**.
        - Replace **<FIELD_NAME>** with **column name**.
        - Replace **<VALUE>** with **valid value corresponding to column name**.
        - Execution
            
                python3 insert_sample.py
- [**InvokeConnection**](invoke_connection_sample.py)
    - Invoke connection
    - Configure
        - Replace **<YOUR_VAULT_ID>** with **VAULT ID**.
        - Replace **<YOUR_VAULT_URL>** with **VAULT URL**.
        - Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.
        - Replace **<YOUR_CONNECTION_URL>** with **Connection url**.
        - Replace **<YOUR_CONNECTION_BASIC_AUTH>** with **access token**.
        - Replace value of **requestBody** with your's request body content.
        - Replace value of **pathParams** with your's path params content.

        - Execution
            
                python3 invoke_connection_sample.py
- [**Service account token generation**](sa_token_Sample.py)
    - generates SA Token using path of credentials file.
    - Configure
        - Replace **<YOUR_CREDENTIALS_FILE_PATH>** with relative  path of **SERVICE ACCOUNT CREDENTIAL FILE**.

        - Execution
            
                python3 sa_token_sample.py

- [**Generate Bearer Token From Credentails**](generate_bearer_token_from_creds_sample.py)
    - generates SA Token using json content of credentials file.
    - Configure
        - Replace **credentials*** with json data of downloaded credentials file while creation Service account.

        - Execution
            
                python3 generate_bearer_token_from_creds_sample.py
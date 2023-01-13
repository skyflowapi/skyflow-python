# Python SDK samples

Test the SDK by adding `VAULT-ID`, `VAULT-URL`, and `SERVICE-ACCOUNT` details in
the required places for each sample.

## Prerequisites
- A Skyflow account. If you don't have one, register for one on the
  [Try Skyflow](https://skyflow.com/try-skyflow) page.
- Python 3.7.0 or higher.

## Prepare

### Install the Python SDK

```bash
pip install skyflow
```

### Create the vault

1. In a browser, sign in to Skyflow Studio.
2. Create a vault by clicking **Create Vault** > **Start With a Template** >
   **Quickstart vault**.
3. Once the vault is ready, click the gear icon and select **Edit Vault Details**.
4. Note your **Vault URL** and **Vault ID** values, then click **Cancel**.
   You'll need these later.

### Create a service account

1. In the side navigation click, **IAM** > **Service Accounts** > **New Service Account**.
2. For **Name**, enter "SDK Sample". For **Roles**, choose **Vault Editor**.
3. Click **Create**. Your browser downloads a **credentials.json** file. Keep
   this file secure, as You'll need it for each of the samples.

## The samples
### [Get data](./get_sample.py)

To retrieve data using Skyflow IDs or unique column values, use the `get(records: dict)` method. The `records` parameter takes a Dictionary that contains either an array of Skyflow IDs or a unique column name and values.

Note: You can use either Skyflow IDs  or `unique` values to retrieve records. You can't use both at the same time.
#### Configure

Replace the following values in the sample file:

| Value                          | Description                                             |
| ------------------------------ | ------------------------------------------------------- |
| `<YOUR_VAULT_ID>`              | ID of your vault.                                       |
| `<YOUR_VAULT_URL>`             | URL of your vault.                                      |
| `<YOUR_CREDENTIALS_FILE_PATH>` | relative path to your service account credentials file. |
| `<TABLE_NAME>`                 | Name of the table to insert data into.                  |
| `<REDACTION_TYPE>`             | One of the four Redaction Types.                        |
| `<SKYFLOW_ID>`                 | Skyflow Id of the record to be fetched.                 |
| `<UNQIUE_COLUMN_NAME>`         | Unique column name to fetch the data.                   |
| `<COLUMN_VALUE>`               | Column value of the corresponding column.               |

#### Run the sample

```bash
python3 get_sample.py
```
### [Get data by ID](./get_by_ids_sample.py)

Get data using Skyflow IDs for the desired records.

#### Configure

Replace the following values in the sample file:

| Value                          | Description                                             |
| ------------------------------ | ------------------------------------------------------- |
| `<YOUR_VAULT_ID>`              | ID of your vault.                                       |
| `<YOUR_VAULT_URL>`             | URL of your vault.                                      |
| `<SKYFLOW_ID1>`                | Skyflow ID of the first record.                         |
| `<SKYFLOW_ID2>`                | Skyflow ID of the second record.                        |
| `<SKYFLOW_ID3>`                | Skyflow ID of the third record.                         |
| `<YOUR_CREDENTIALS_FILE_PATH>` | relative path to your service account credentials file. |
| `<TABLE_NAME>`                 | Name of the table to get data from.                     |

#### Run the sample

```bash
python3 get_by_ids_sample.py
```


### [Update data](./update_sample.py)

Update data in the vault.

#### Configure

Replace the following values in the sample file:

| Value                          | Description                                             |
| ------------------------------ | ------------------------------------------------------- |
| `<YOUR_VAULT_ID>`              | ID of your vault.                                       |
| `<YOUR_VAULT_URL>`             | URL of your vault.                                      |
| `<YOUR_CREDENTIALS_FILE_PATH>` | relative path to your service account credentials file. |
| `<TABLE_NAME>`                 | Name of the table to insert data into.                  |
| `<SKYFLOW_ID>`                 | Skyflow Id of the record to be updated.                 |
| `<FIELD_NAME>`                 | Name of the column to update data.                      |
| `<VALUE>`                      | Valid value to update into the corresponding column.    |

#### Run the sample

```bash
python3 update_sample.py
```

### [Insert data](./insert_sample.py)

Insert data in the vault.

#### Configure

Replace the following values in the sample file:

| Value                          | Description                                             |
| ------------------------------ | ------------------------------------------------------- |
| `<YOUR_VAULT_ID>`              | ID of your vault.                                       |
| `<YOUR_VAULT_URL>`             | URL of your vault.                                      |
| `<YOUR_CREDENTIALS_FILE_PATH>` | relative path to your service account credentials file. |
| `<TABLE_NAME>`                 | Name of the table to insert data into.                  |
| `<FIELD_NAME>`                 | Name of the column to insert data into.                 |
| `<VALUE>`                      | Valid value to insert into the corresponding column.    |

#### Run the sample

```bash
python3 insert_sample.py
```

### [Detokenize data](./detokenize_sample.py)

Detokenize a data token from the vault. Make sure the specified token is for
data that exists in the vault. If you need a valid token, use
[insert_sample.py](insert_sample.py) to insert the data, then use this data's
token for detokenization.

#### Configure

Replace the following values in the sample file:

| Value                          | Description                                             |
| ------------------------------ | ------------------------------------------------------- |
| `<YOUR_VAULT_ID>`              | ID of your vault.                                       |
| `<YOUR_VAULT_URL>`             | URL of your vault.                                      |
| `<YOUR_CREDENTIALS_FILE_PATH>` | relative path to your service account credentials file. |
| `<FIELD_NAME>`                 | Name of the column to insert data into.                 |
| `<TOKEN>`                      | Token for the data you want to detokenize.              |

#### Run the sample

```bash
python3 detokenize_sample.py
```

### [Invoke a connection](./invoke_connection_sample.py)

Skyflow Connections is a gateway service that uses Skyflow's underlying
tokenization capabilities to securely connect to first-party and third-party
services. This way, your infrastructure is never directly exposed to sensitive
data, and you offload security and compliance requirements to Skyflow.

#### Configure

Replace the following values in the sample file:

| Value                          | Description                                             |
| ------------------------------ | ------------------------------------------------------- |
| `<YOUR_VAULT_ID>`              | ID of your vault.                                       |
| `<YOUR_VAULT_URL>`             | URL of your vault.                                      |
| `<YOUR_CREDENTIALS_FILE_PATH>` | relative path to your service account credentials file. |
| `<YOUR_CONNECTION_URL>`        | URL of your connection.                                 |
| `<YOUR_CONNECTION_BASIC_AUTH>` | Access token for your connection.                       |
| `requestBody`                  | Your request body content.                              |
| `pathParams`                   | Your path parameters.                                   |

#### Run the sample

```bash
python3 invoke_connection_sample.py
```

### [Service account token generation](./sa_token_sample.py)

Generates SA Token using path of credentials file.

#### Configure

Replace `<YOUR_CREDENTIALS_FILE_PATH>` with the relative path to your service account credentials file.

#### Run the sample

```bash
python3 sa_token_sample.py
```

### [Generate Bearer Token](./generate_bearer_token_from_creds_sample.py)

Generates SA Token using json content of credentials file.

#### Configure

Replace `credentials` with the content of service account credentials file.

#### Run the sample

```bash
python3 generate_bearer_token_from_creds_sample.py
```

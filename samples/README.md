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

### [Get data by ID](./getByIDSample.py)

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
python3 getByIDSample.py
```

### [Insert data](./InsertSample.py)

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
python3 InsertSample.py
```

### [Detokenize data](./detokenizeSample.py)

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
python3 detokenizeSample.py
```

### [Invoke a connection](./invokeConnectionSample.py)

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
python3 invokeConnectionSample.py
```

### [Service account token generation](./SATokenSample.py)

Generates SA Token using path of credentials file.

#### Configure

Replace `<YOUR_CREDENTIALS_FILE_PATH>` with the relative path to your service account credentials file.

#### Run the sample

```bash
python3 SATokenSample.py
```

### [Generate Bearer Token](./generateBearerTokenFromCredsSample.py)

Generates SA Token using json content of credentials file.

#### Configure

Replace `credentials` with the content of service account credentials file.

#### Run the sample

```bash
python3 generateBearerTokenFromCredsSample.py
```

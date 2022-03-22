## Description
These are the samples for skyflow-python. In order to use these samples, you must first:

1. Install skyflow module using pip
2. Replace placeholders like `<YOU_VAULT_ID>`, `<YOUR_VAULT_URL>` etc. in the sample file with your Vault ID, Vault URL etc.

Below is a brief description of the samples:

- [SATokenSample.py](https://github.com/skyflowapi/skyflow-python/blob/main/samples/SATokenSample.py): Contains a python program illustrating the usage of `service_account.generate_bearer_token()`
- [InsertSample.py](https://github.com/skyflowapi/skyflow-python/blob/main/samples/InsertSample.py) : Contains a python program illustrating the use of `vault.Client.insert()`
- [detokenizeSample.py](https://github.com/skyflowapi/skyflow-python/blob/main/samples/detokenizeSample.py): Contains a python program illustrating the use of `vault.detokenize()`
- [`getByIDSample.py`](https://github.com/skyflowapi/skyflow-python/blob/main/samples/getByIDSample.py): Contains a python program illustrating the use of `vault.Client.get_by_id()`
- [`invoke_connection.py`](https://github.com/skyflowapi/skyflow-python/blob/main/samples/invoke_connectionSample.py): Contains a python program illustrating the use of `vault.Client.invoke_connection()`
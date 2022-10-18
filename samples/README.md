## Description
These are the samples for skyflow-python. In order to use these samples, you must first:

1. Install skyflow module using pip
2. Replace placeholders like `<YOU_VAULT_ID>`, `<YOUR_VAULT_URL>` etc. in the sample file with your Vault ID, Vault URL etc.

Below is a brief description of the samples:

- [sa_token_sample.py](https://github.com/skyflowapi/skyflow-python/blob/main/samples/sa_token_sample.py): Contains a python program illustrating the usage of `service_account.generate_bearer_token()`
- [insert_sample.py](https://github.com/skyflowapi/skyflow-python/blob/main/samples/insert_sample.py) : Contains a python program illustrating the use of `vault.Client.insert()`
- [detokenize_sample.py](https://github.com/skyflowapi/skyflow-python/blob/main/samples/detokenize_sample.py): Contains a python program illustrating the use of `vault.detokenize()`
- [`get_by_ids_sample.py`](https://github.com/skyflowapi/skyflow-python/blob/main/samples/get_by_ids_sample.py): Contains a python program illustrating the use of `vault.Client.get_by_id()`
- [`invoke_connection_sample.py`](https://github.com/skyflowapi/skyflow-python/blob/main/samples/invoke_connection_sample.py): Contains a python program illustrating the use of `vault.Client.invoke_connection()`
# Skyflow Python SDK — v2 (PDB) and v3 (FlowDB) Installation

## v2 — PDB SDK

### Install

```bash
pip install "skyflow-python==2.0.0"
```

### Initialize client

```python
from skyflow import SkyflowClient, SkyflowConfig, Credentials

client = SkyflowClient(
    SkyflowConfig(
        vault_id="<VAULT_ID>",
        cluster_id="<CLUSTER_ID>",
        credentials=Credentials(api_key="<API_KEY>"),
    )
)
```

### Insert

```python
from skyflow import InsertRequest

response = client.vault().insert(
    InsertRequest(
        table="cards",
        values=[{"card_number": "4111111111111111", "cardholder_name": "John Doe"}],
        return_tokens=True,
    )
)
print(response)
# {"records": [{"skyflow_id": "...", "table": "cards"}], "errors": []}
```

---

## v3 — FlowDB SDK

### Install

```bash
pip install "skyflow-python==3.0.0"
```

### Initialize client

```python
from skyflow import SkyflowClient, SkyflowConfig, Credentials

client = SkyflowClient(
    SkyflowConfig(
        vault_id="<VAULT_ID>",
        cluster_id="<CLUSTER_ID>",
        credentials=Credentials(api_key="<API_KEY>"),
    )
)
```

### Insert

```python
from skyflow import InsertRequest

response = client.vault().insert(
    InsertRequest(
        table="records",
        values=[{"field_name": "value"}],
    )
)
print(response)
# {"records": [{"skyflow_id": "...", "table": "records"}], "errors": []}
```

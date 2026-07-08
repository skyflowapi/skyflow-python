"""Contract adapter for v3 (flowvault). See v2_adapter.py for the shared design note -- import
this module only from a flowvault-installed environment (`SKYFLOW_TEST_VARIANT=v3`)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from skyflow_flowvault.vault.client.client import VaultClient
from skyflow_flowvault.vault.controller import VaultController
from skyflow_flowvault.vault.data import InsertRequest


def build_vault():
    config = {
        "vault_id": "contract_vault",
        "cluster_id": "contract_cluster",
        "env": "PROD",
        "credentials": {"token": "contract_static_token"},
    }
    vault_client = VaultClient(config)
    vault_client.initialize_client_configuration = MagicMock()  # skip real credential/URL resolution
    insert_api = MagicMock()
    vault_client.get_insert_api = MagicMock(return_value=insert_api)
    vault = VaultController(vault_client)
    return vault, insert_api


def build_insert_request(n):
    return InsertRequest(table="contract_table", records=[dict(values={"field": f"value{i}"}) for i in range(n)])


def call_insert(vault, insert_api, request):
    def fake_insert(**kwargs):
        records = [
            SimpleNamespace(skyflow_id=f"id{i}", tokens=None, data=None, error=None, http_code=None, table_name=None)
            for i in range(len(kwargs["records"]))
        ]
        return SimpleNamespace(data=SimpleNamespace(records=records), headers={})

    insert_api.with_raw_response.insert.side_effect = fake_insert
    response = vault.insert(request)
    call_count = insert_api.with_raw_response.insert.call_count
    return response, call_count


# v3's InsertResponse now shares the exact same shape as v2's (inserted_fields/errors, each
# entry tagged request_index) -- kept as separate accessor functions per adapter anyway, since
# the contract module intentionally treats each variant's response as opaque.
def count_successes(response):
    return len(response.inserted_fields)


def count_errors(response):
    return len(response.errors) if response.errors else 0

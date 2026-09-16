"""Contract adapter for v2. Constructs a Vault with its underlying generated API call mocked
out, so the contract suite can assert on SDK-level behavior (call counts, response shape)
without needing real network access or credentials. Import this module only from a v2-installed
environment (`SKYFLOW_TEST_VARIANT=v2`) -- v2.skyflow and v3.skyflow cannot coexist in one
process."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from skyflow.vault.client.client import VaultClient
from skyflow.vault.controller import Vault
from skyflow.vault.data import InsertRequest

# Uses the public `Vault` alias deliberately (not VaultController) -- this adapter simulates
# an external consumer, and Vault is the name they'd actually import.


def build_vault():
    config = {
        "vault_id": "contract_vault",
        "cluster_id": "contract_cluster",
        "env": "PROD",
        "credentials": {"token": "contract_static_token"},
    }
    vault_client = VaultClient(config)
    vault_client.initialize_client_configuration = MagicMock()  # skip real credential/URL resolution
    records_api = MagicMock()
    vault_client.get_records_api = MagicMock(return_value=records_api)
    vault = Vault(vault_client)
    return vault, records_api


def build_insert_request(n):
    return InsertRequest(table="contract_table", values=[{"field": f"value{i}"} for i in range(n)])


def call_insert(vault, records_api, request):
    fake_records = [SimpleNamespace(skyflow_id=f"id{i}", tokens=None) for i in range(len(request.values))]
    fake_response = SimpleNamespace(data=SimpleNamespace(records=fake_records), headers={})
    records_api.with_raw_response.record_service_insert_record.return_value = fake_response

    response = vault.insert(request)
    call_count = records_api.with_raw_response.record_service_insert_record.call_count
    return response, call_count


# v2's InsertResponse is the shared shape (inserted_fields/errors) both variants now use.
def count_successes(response):
    return len(response.inserted_fields)


def count_errors(response):
    return len(response.errors) if response.errors else 0

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

# v2 never batches this round -- it's excluded from VaultController's shared batching loop
# entirely (see the plan's Decisions section: v2 must remain byte-for-byte behaviorally
# identical, and today it always sends every record in a single HTTP call). Uses the public
# `Vault` alias deliberately (not PdbVaultController) -- this adapter simulates an external
# consumer, and Vault is the name they'd actually import.
SUPPORTS_BATCHING = False


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


# v2's InsertResponse (inserted_fields/errors) and v3's (summary/success/errors -- ported from
# Java's v3 reference for response-shape parity) are no longer the same vocabulary by design; the
# contract only asserts that BOTH correctly report counts, via these two accessors, rather than
# pretending the underlying shapes still match.
def count_successes(response):
    return len(response.inserted_fields)


def count_errors(response):
    return len(response.errors) if response.errors else 0

"""Type-check fixture, not a test file to be executed directly (see test_typecheck_contract.py).

Every construction below uses a v2-only InsertRequest keyword argument that does not exist on
flowvault's InsertRequest (records/table/upsert only -- see
flowvault/skyflow_flowvault/vault/data/_insert_request.py). Run under mypy/pyright against a
flowvault install, each of these lines must be flagged as a type error. If a future change to
flowvault's InsertRequest ever silently grows one of these fields back, this fixture stops
producing errors and test_typecheck_contract.py's assertion on it fails -- that's the point:
it's a regression trip-wire, not a demonstration.

No `# type: ignore` anywhere in this file -- the whole point is for the checker to actually emit
diagnostics.
"""
from skyflow_flowvault.vault.data import InsertRequest

InsertRequest(records=[], table="t1", homogeneous=True)
InsertRequest(records=[], table="t1", continue_on_error=True)
InsertRequest(records=[], table="t1", token_mode="ENABLE")
InsertRequest(records=[], table="t1", return_tokens=False)

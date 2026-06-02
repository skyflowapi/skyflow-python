# Onboarding & Documentation Backlog

**Status:** Triage backlog (not an implementation plan)
**Created:** 2026-06-02
**Scope:** Consolidates two audits of the Skyflow Python SDK into one prioritized, pick-up-ready backlog. Implementation scope/sequencing to be decided by the team during triage.

## Source audits

This document merges and de-duplicates:

1. **Onboarding / first-run audit** — focuses on time-to-first-success, correctness drift between docs and code, packaging/typing, and contributor onboarding. (Captured in this repo.)
2. **API-coverage audit** — Confluence page *"Python"* (space `SDK1`), which catalogues ~80+ public interfaces and finds ~35+ undocumented in the README: <https://skyflow.atlassian.net/wiki/spaces/SDK1/pages/2949873695/Python>

## Executive summary

The README is genuinely comprehensive and well-structured (clear ToC, consistent "construct request → call → print" pattern, runnable sample links, a real v1→v2 migration guide). The gaps are **not** about missing breadth. They cluster into three themes:

- **Correctness drift** — the docs contradict the code in ways that break or mislead a new user before they write any code (e.g. Python version requirement).
- **Hard first-run barrier** — the quickstart assumes the user already has a vault, cluster ID, credentials, and a matching table; there is no "zero-to-running" / sandbox path, and **no operation shows its response shape**.
- **Undocumented public surface** — ~35+ exported enums, response classes, request parameters, and client-management methods never appear in the README, forcing users to read source.

Legend: **Priority** P0 (broken/misleading) · P1 (high friction) · P2 (polish / bigger bet). **Effort** S (hours) · M (1–3 days) · L (week+). **Source** Onboarding · API-coverage · Both.

Evidence tagging: claims verified against code carry a `file:line` reference. Items sourced from the API-coverage audit but **not yet re-verified in code** are marked _(unverified)_ so triage knows what still needs a code check.

---

## Prioritized summary

| ID | Title | Category | Priority | Effort | Source |
|----|-------|----------|----------|--------|--------|
| OB-1 | Python version contradiction (3.8 in README vs 3.9 in setup.py) | Correctness | P0 | S | Onboarding |
| OB-2 | "async" sample is actually thread-pool concurrency (misleading) | Correctness | P0 | S | Onboarding |
| OB-3 | Document response-object shapes for every operation | README-content | P1 | M | Both |
| OB-4 | Add `skyflow/py.typed` (PEP 561) for IDE/type-checker support | Packaging/Typing | P1 | S | Onboarding |
| OB-5 | Add "Get your credentials" / sandbox first-run section | README-content | P1 | M | Onboarding |
| OB-6 | Add a Troubleshooting / common-errors section | README-content | P1 | M | Onboarding |
| OB-7 | Document undocumented request parameters | README-content | P1 | M | API-coverage |
| OB-8 | Document undocumented enums (TokenMode, etc.) | README-content | P1 | S | API-coverage |
| OB-9 | Document Skyflow client-management methods | README-content | P1 | S | API-coverage |
| OB-10 | Document `is_expired` & `generate_signed_data_tokens_from_creds` | README-content | P1 | S | API-coverage |
| OB-11 | Add `samples/README.md` + `.env.example` | Samples | P1 | M | Onboarding |
| OB-12 | Document client lifecycle / thread-safety / retries | README-content | P1 | M | Onboarding |
| OB-13 | Document Detect helper classes (EntityInfo, TextIndex, Bleep, File) | README-content | P2 | M | API-coverage |
| OB-14 | Add README badges (PyPI, Python versions, build, license) | Polish | P2 | S | Onboarding |
| OB-15 | Align `requirements.txt` ↔ `setup.py` dependency drift | Correctness | P2 | S | Onboarding |
| OB-16 | Remove/clean up `UploadFileRequest` empty stub | Cleanup | P2 | S | API-coverage |
| OB-17 | Typed config/request objects (TypedDict or pydantic) | Bigger-bet | P2 | L | Onboarding |
| OB-18 | Hosted API reference (Sphinx → ReadTheDocs) + split README | Bigger-bet | P2 | L | Onboarding |
| OB-19 | Framework integration guides (Django/Flask/FastAPI) | Bigger-bet | P2 | L | Onboarding |
| OB-20 | Add CONTRIBUTING.md, issue templates, CODE_OF_CONDUCT | Contributor | P2 | M | Onboarding |

---

## P0 — Broken or misleading (fix first)

### OB-1 · Python version contradiction
*Priority P0 · Effort S · Correctness · Onboarding*

**Problem:** The README states Python 3.8 is supported and tested, but the package requires 3.9+. A 3.8 user follows the README and `pip install`/import fails before writing any code.
- [README.md:81](../README.md#L81): *"Python 3.8.0 and above (tested with Python 3.8.0)"*
- [setup.py:8](../setup.py#L8): `raise RuntimeError("skyflow requires Python 3.9+")`, plus `python_requires=">=3.9"`.

**Proposed fix:** Decide the real floor (3.9 per `setup.py`) and make README, `setup.py`, and any CI matrix agree. Update the README "Require" line and the "tested with" claim to match what CI actually tests.

**Acceptance criteria:** README, `setup.py`, and CI declare the same minimum Python version; the "tested with" version matches an actual CI job.

### OB-2 · Misleading "async" sample
*Priority P0 · Effort S · Correctness · Onboarding*

**Problem:** [samples/detect_api/deidentify_file_async.py](../samples/detect_api/deidentify_file_async.py) is named "async" but uses `concurrent.futures.ThreadPoolExecutor` — the SDK is sync-only (no `async def`/`await` in the package). The name implies asyncio support that does not exist.

**Proposed fix:** Rename to convey thread-based concurrency (e.g. `deidentify_file_concurrent.py`) and/or add a comment clarifying the threading model. If/when true async is on the roadmap, note it explicitly instead.

**Acceptance criteria:** Sample name/comments accurately reflect that concurrency is thread-based, not asyncio. No doc implies `await`-able clients exist.

---

## P1 — High friction (core of the effort)

### OB-3 · Document response-object shapes
*Priority P1 · Effort M · README-content · Both*

**Problem:** Every README example ends with `print(...response)`, but the README never shows what comes back. Response classes and their attributes are undocumented — users must read source or guess. Verified attributes:
- `InsertResponse` → `inserted_fields`, `errors` ([_insert_response.py](../skyflow/vault/data/_insert_response.py))
- Per the API-coverage audit _(unverified beyond InsertResponse)_: `GetResponse(data, errors)`, `DeleteResponse(deleted_ids, errors)`, `UpdateResponse(updated_field, errors)`, `QueryResponse(fields, errors)`, `FileUploadResponse(skyflow_id, errors)`, `DetokenizeResponse(detokenized_fields, errors)`, `TokenizeResponse(tokenized_fields, errors)`, `InvokeConnectionResponse(data, metadata, errors)`, `DeidentifyTextResponse(processed_text, entities, word_count, char_count)`, `ReidentifyTextResponse(processed_text)`, `DeidentifyFileResponse(file_base64, file, type, extension, word_count, char_count, size_in_kb, duration_in_seconds, page_count, slide_count, entities, run_id, status)`.

**Proposed fix:** For each operation, add an "Example response" block showing the object and its attributes. Verify each attribute list against source before publishing.

**Acceptance criteria:** Every documented operation shows its response object and attributes; all attribute lists verified against the response class source.

### OB-4 · Add `skyflow/py.typed`
*Priority P1 · Effort S · Packaging/Typing · Onboarding*

**Problem:** A `py.typed` marker exists only at `skyflow/generated/rest/py.typed`, not at the top-level `skyflow/` package. Per PEP 561, mypy/pyright therefore treat the public SDK as untyped — no autocomplete on `InsertRequest(...)`, no inline type errors — despite the package shipping pydantic.

**Proposed fix:** Add an empty `skyflow/py.typed` and ensure it's included in the wheel (`package_data`/`include_package_data` in `setup.py`).

**Acceptance criteria:** `import skyflow` resolves types under mypy/pyright in a consuming project; `py.typed` ships in the built wheel.

### OB-5 · "Get your credentials" / sandbox first-run section
*Priority P1 · Effort M · README-content · Onboarding*

**Problem:** The quickstart ([README.md:91](../README.md#L91)) assumes the user already has `vault_id`, `cluster_id`, an `api_key`, and a table named `table1` with matching columns. Nothing explains how to obtain these. A brand-new user cannot run the first example.

**Proposed fix:** Add a short pre-quickstart section: where to find `vault_id`/`cluster_id` (the `{clusterId}.vault.skyflowapis.com` URL), how to create a service account / API key, and the minimal table/schema the quickstart assumes. Link to the relevant Skyflow console docs. If a sandbox/test environment exists, show the no-setup path.

**Acceptance criteria:** A new user can go from "fresh account" to a successful first call using only the README; every placeholder in the quickstart has a "where this comes from" pointer.

### OB-6 · Troubleshooting / common-errors section
*Priority P1 · Effort M · README-content · Onboarding*

**Problem:** Only the bearer-token-expiry edge case is documented ([README.md:850](../README.md#L850)). The errors new users actually hit — wrong `cluster_id`, wrong `env`, 403 (missing role permission), table/column not found — have no guidance.

**Proposed fix:** Add an "error → likely cause → fix" table covering the top first-run failures, plus how to read `SkyflowError` (`http_code`, `message`, `details`).

**Acceptance criteria:** Section covers the top ~8–10 first-run errors with actionable fixes.

### OB-7 · Document undocumented request parameters
*Priority P1 · Effort M · README-content · API-coverage_(unverified)_*

**Problem:** Several request parameters are exported and usable but absent from the README:
- `InsertRequest`: `tokens`, `homogeneous`, `token_mode`
- `UpdateRequest`: `tokens`, `token_mode`
- `GetRequest`: `fields`, `offset`, `limit`, `download_url` (field selection + pagination — commonly needed)
- `FileUploadRequest`: `file_path`, `base64`, `file_name`
- `FileInput`: `file_path`
- `DeidentifyFileRequest`: `allow_regex_list`, `restrict_regex_list`, `output_processed_image`, `output_ocr_text`, `masking_method`, `pixel_density`, `max_resolution`, `output_processed_audio`, `output_transcription`, `bleep`
- `DeidentifyTextRequest`: `allow_regex_list`, `restrict_regex_list`

**Proposed fix:** Document each parameter (name, default, purpose) on the relevant request. Verify defaults against source before publishing. Prioritize `GetRequest` pagination and `InsertRequest`/`UpdateRequest` `token_mode`/`tokens` (BYOT).

**Acceptance criteria:** Each request's documented parameter list matches its constructor signature; defaults verified.

### OB-8 · Document undocumented enums
*Priority P1 · Effort S · README-content · API-coverage*

**Problem:** Exported from `skyflow.utils.enums` ([__init__.py](../skyflow/utils/enums/__init__.py), verified) but undocumented:
- `TokenMode` → `DISABLE`, `ENABLE`, `ENABLE_STRICT` (verified, [token_mode.py](../skyflow/utils/enums/token_mode.py)) — used by Insert/Update for BYOT.
- `MaskingMethod` → `BLACKBOX`/`BLUR` (verified, [masking_method.py](../skyflow/utils/enums/masking_method.py)).
- `TokenType` full set (`VAULT_TOKEN`, `ENTITY_UNIQUE_COUNTER`, `ENTITY_ONLY`) — only two values shown in Detect examples.
- `ContentType` (`JSON`, `PLAINTEXT`, `XML`, `URLENCODED`, `FORMDATA`), `DetectOutputTranscriptions`, `Env` non-PROD variants (`SANDBOX`, `DEV`, `STAGE`), `EnvUrls`, `RequestMethod.NONE`. _(values unverified)_

**Proposed fix:** Add a concise enum reference (table per enum) and link from the operations that consume them.

**Acceptance criteria:** Every user-facing enum and its values are listed; values verified against source.

### OB-9 · Document Skyflow client-management methods
*Priority P1 · Effort S · README-content · API-coverage*

**Problem:** The README documents only the builder methods and `vault()/connection()/detect()` accessors. These public methods (verified in [skyflow/client/skyflow.py:27-67](../skyflow/client/skyflow.py#L27)) are undocumented:
`remove_vault_config`, `update_vault_config`, `get_vault_config`, `add_connection_config`, `remove_connection_config`, `update_connection_config`, `get_connection_config`, `add_skyflow_credentials`, `update_skyflow_credentials`, `update_log_level`, `get_log_level`.

**Proposed fix:** Add a "Managing the client after build" subsection documenting post-build config mutation and log-level control.

**Acceptance criteria:** All public, non-builder client methods are documented with signatures and purpose.

### OB-10 · Document `is_expired` & `generate_signed_data_tokens_from_creds`
*Priority P1 · Effort S · README-content · API-coverage*

**Problem:** Both are exported from `skyflow.service_account` (verified, [service_account/__init__.py](../skyflow/service_account/__init__.py)) but undocumented. `is_expired(token)` is commonly needed for token-lifecycle management; `generate_signed_data_tokens_from_creds` is the string-based counterpart to the documented file-path function.

**Proposed fix:** Document both alongside the existing token-generation docs, mirroring the `_from_creds` pattern already shown for bearer tokens.

**Acceptance criteria:** Both functions documented with a usage snippet.

### OB-11 · `samples/README.md` + `.env.example`
*Priority P1 · Effort M · Samples · Onboarding*

**Problem:** 22 sample files across `samples/{vault_api,detect_api,service_account}` have no README and no env template; each hardcodes `<PLACEHOLDERS>`. There's no `cp .env.example .env` flow to make them runnable.

**Proposed fix:** Add `samples/README.md` (prerequisites, how to run, what each sample shows) and a `.env.example` with the variables the samples read. Optionally refactor samples to load from env.

**Acceptance criteria:** A user can run any sample by copying `.env.example`, filling values, and following `samples/README.md`.

### OB-12 · Client lifecycle / thread-safety / retries
*Priority P1 · Effort M · README-content · Onboarding*

**Problem:** The stated audience is Python backends, but the README never says whether `Skyflow` is thread-safe, should be reused as a singleton vs rebuilt per request, or how retries/timeouts/connection pooling are configured.

**Proposed fix:** Add a short "Using the client in production" section covering reuse/lifecycle, thread-safety, and any timeout/retry configuration. Verify behavior against the client implementation before documenting.

**Acceptance criteria:** Section answers reuse, thread-safety, and timeout/retry questions; claims verified against code.

---

## P2 — Polish & bigger bets

### OB-13 · Document Detect helper classes
*Priority P2 · Effort M · README-content · API-coverage_(unverified)_*

**Problem:** Publicly exported from `skyflow.vault.detect` but undocumented: `EntityInfo` (`token`, `value`, `text_index`, `processed_index`, `entity`, `scores`), `TextIndex` (`start`, `end`), `Bleep` (`gain`, `frequency`, `start_padding`, `stop_padding`), and the Detect `File` wrapper (`name`, `size`, `type`, `last_modified`, `read()`, `seek()`).

**Proposed fix:** Document these as part of the Detect response/request reference. Verify attributes against source.

**Acceptance criteria:** Each helper class documented with attributes/methods; verified.

### OB-14 · README badges
*Priority P2 · Effort S · Polish · Onboarding*

**Problem:** The README has zero badges (verified). No PyPI version, supported-Python, build, coverage, or license signal at a glance.

**Proposed fix:** Add standard badges to the README header.

**Acceptance criteria:** Header shows at least PyPI version, supported Python versions, build status, and license.

### OB-15 · Align `requirements.txt` ↔ `setup.py`
*Priority P2 · Effort S · Correctness · Onboarding*

**Problem:** Dependency drift, e.g. `setuptools >= 21.0.0` ([requirements.txt](../requirements.txt)) vs `setuptools >= 75.3.3` ([setup.py:31](../setup.py#L31)). Risk of inconsistent installs.

**Proposed fix:** Reconcile the two (or generate one from the other) so version constraints match.

**Acceptance criteria:** No conflicting version constraints between the two files.

### OB-16 · Clean up `UploadFileRequest` stub
*Priority P2 · Effort S · Cleanup · API-coverage*

**Problem:** `UploadFileRequest` is an exported empty stub (`def __init__(self): pass`, verified [_upload_file_request.py](../skyflow/vault/data/_upload_file_request.py)), apparently superseded by `FileUploadRequest`. It pollutes the public surface.

**Proposed fix:** Remove from exports (or document if it has a real purpose). Treat as a potential breaking change — confirm nothing depends on it and gate on a minor/major version bump.

**Acceptance criteria:** `UploadFileRequest` is either removed from the public API or documented with a clear purpose; release notes mention the change if removed.

### OB-17 · Typed config/request objects
*Priority P2 · Effort L · Bigger-bet · Onboarding*

**Problem:** Config and credentials are untyped dicts (`{'vault_id': ..., 'cluster_id': ...}`), so a typo like `'clster_id'` fails at runtime instead of at edit time. The SDK already depends on pydantic but users get none of the type safety on inputs.

**Proposed fix:** Offer `TypedDict` (or pydantic model) variants for config/credentials and request constructors, keeping dict input for back-compat. Design as an additive, non-breaking enhancement.

**Acceptance criteria:** Users get autocomplete and static validation on config/request inputs without breaking existing dict-based usage.

### OB-18 · Hosted API reference + README split
*Priority P2 · Effort L · Bigger-bet · Onboarding*

**Problem:** Public modules are `_`-prefixed, so users have only the 870-line README — no generated API reference. The single file is hard to scan for onboarding vs reference use.

**Proposed fix:** Generate a hosted API reference (Sphinx → ReadTheDocs) from docstrings and split the README into a short "Getting Started" plus a linked reference. (Depends on docstring coverage — may pair with OB-3/OB-7/OB-8.)

**Acceptance criteria:** A hosted, versioned API reference exists; README is scannable for first-run vs deep reference.

### OB-19 · Framework integration guides
*Priority P2 · Effort L · Bigger-bet · Onboarding*

**Problem:** No examples for the most common backends (Django/Flask/FastAPI), including where to construct/reuse the client. (Pairs with OB-12.)

**Proposed fix:** Add one focused integration example per major framework showing client lifecycle and a representative operation.

**Acceptance criteria:** At least one runnable integration example each for Django, Flask, and FastAPI.

### OB-20 · Contributor onboarding files
*Priority P2 · Effort M · Contributor · Onboarding*

**Problem:** No `CONTRIBUTING.md`, issue templates, or `CODE_OF_CONDUCT.md` (only a PR template exists under `.github/workflows/`). Blocks contributor onboarding; the PR template is also in a non-standard location.

**Proposed fix:** Add `CONTRIBUTING.md` (dev setup, test/lint commands, branch/release flow), issue templates, and a code of conduct. Move the PR template to the conventional `.github/` root if appropriate.

**Acceptance criteria:** Standard GitHub community-health files present and discoverable.

---

## Appendix: full undocumented-interface inventory

Reproduced from the API-coverage audit for completeness so nothing is lost as README items close. Verified entries are tagged; the rest are _(unverified)_ pending a code check during implementation.

### Enums (exported from `skyflow.utils.enums`, export list verified)
| Enum | Values | Notes |
|------|--------|-------|
| `EnvUrls` | — | Internal but exported _(unverified)_ |
| `ContentType` | `JSON`, `PLAINTEXT`, `XML`, `URLENCODED`, `FORMDATA` | _(values unverified)_ |
| `TokenMode` | `DISABLE`, `ENABLE`, `ENABLE_STRICT` | Verified; used by Insert/Update (BYOT) |
| `TokenType` | `VAULT_TOKEN`, `ENTITY_UNIQUE_COUNTER`, `ENTITY_ONLY` | Partially documented; full set _(unverified)_ |
| `DetectOutputTranscriptions` | `DIARIZED_TRANSCRIPTION`, `MEDICAL_DIARIZED_TRANSCRIPTION`, `MEDICAL_TRANSCRIPTION`, `TRANSCRIPTION` | _(values unverified)_ |
| `MaskingMethod` | `BLACKBOX` (`blackbox`), `BLUR` (`blur`) | Verified |
| `Env` non-PROD | `SANDBOX`, `DEV`, `STAGE` | Only `PROD` shown in README _(unverified)_ |
| `RequestMethod.NONE` | — | `GET/POST/PUT/PATCH/DELETE` documented; `NONE` not _(unverified)_ |

### Response classes (attributes per API-coverage audit; only `InsertResponse` verified here)
`InsertResponse(inserted_fields, errors)` ✓ · `GetResponse(data, errors)` · `DeleteResponse(deleted_ids, errors)` · `UpdateResponse(updated_field, errors)` · `QueryResponse(fields, errors)` · `FileUploadResponse(skyflow_id, errors)` · `DetokenizeResponse(detokenized_fields, errors)` · `TokenizeResponse(tokenized_fields, errors)` · `InvokeConnectionResponse(data, metadata, errors)` · `DeidentifyTextResponse(processed_text, entities, word_count, char_count)` · `ReidentifyTextResponse(processed_text)` · `DeidentifyFileResponse(file_base64, file, type, extension, word_count, char_count, size_in_kb, duration_in_seconds, page_count, slide_count, entities, run_id, status)`

### Detect helper classes (exported from `skyflow.vault.detect`)
`EntityInfo(token, value, text_index, processed_index, entity, scores)` · `TextIndex(start, end)` · `Bleep(gain, frequency, start_padding, stop_padding)` · `File(name, size, type, last_modified, read(), seek())` — _(unverified)_

### Client methods (verified, [skyflow/client/skyflow.py:27-67](../skyflow/client/skyflow.py#L27))
`remove_vault_config`, `update_vault_config`, `get_vault_config`, `add_connection_config`, `remove_connection_config`, `update_connection_config`, `get_connection_config`, `add_skyflow_credentials`, `update_skyflow_credentials`, `update_log_level`, `get_log_level`

### Service-account functions (verified, [service_account/__init__.py](../skyflow/service_account/__init__.py))
`is_expired(token)`, `generate_signed_data_tokens_from_creds(credentials, options)`

### Cleanup candidates
`UploadFileRequest` (empty stub, verified) · `SkyflowMessages` (exported, internal) · `SDK_VERSION` (exported, undocumented) · `Audit`/`BinLookUp` (stub controllers, **not** exported — not user-reachable, verified [controller/__init__.py](../skyflow/vault/controller/__init__.py))

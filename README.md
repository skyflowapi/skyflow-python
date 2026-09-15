# Skyflow Python SDK

This repository hosts the Skyflow Python SDKs. It is a multi-package workspace — pick the package
that matches the vault you're using.

## Which package do I want?

| Package (PyPI) | Import | Vault type | Docs |
|---|---|---|---|
| **`skyflow`** | `import skyflow` | Privacy DB (v2.x) — vault CRUD, tokenize/detokenize, query, files, Detect, Connections | [skyvault/README.md](skyvault/README.md) |
| **`skyflow-flowvault-python`** | `import skyflow_flowvault` | Flow DB (v1.x) — high-throughput bulk + unary vault operations | [flowvault/README.md](flowvault/README.md) |

```bash
pip install skyflow            # Privacy DB SDK
pip install skyflow-flowvault-python  # Flow DB SDK
```

> The two artifacts have **independent version lines** and cannot be installed into the same Python
> environment at once. A lower `skyflow-flowvault-python` version number (1.x) does not mean it is behind
> `skyflow` (2.x) — they are separate products.

## Repository layout

| Path | What it is |
|---|---|
| `common/` | Shared client, credentials, config, and error code — depended on by both SDKs, never published on its own. |
| `skyvault/` | The `skyflow` (Privacy DB / v2) SDK. |
| `flowvault/` | The `skyflow-flowvault-python` (Flow DB / v1) SDK. |
| `docs/` | Reference docs and the [v1 → v2 migration guide](docs/migrate_to_v2.md). |
| `CHANGELOG.md` | Release history. |

Each SDK ships runnable examples under its own `samples/` directory
([flowvault/samples/](flowvault/samples/), [skyvault/samples/](skyvault/samples/)).

## Resources

- [Skyflow docs](https://docs.skyflow.com/)
- [GitHub](https://github.com/skyflowapi/skyflow-python/)

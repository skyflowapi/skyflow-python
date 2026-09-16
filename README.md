# Skyflow Python SDK

This repository hosts Skyflow's Python SDKs. It is a multi-package workspace — pick the package
that matches the vault you're using.

## Which package do I want?

| Package (PyPI) | Import | Vault type | Docs |
|---|---|---|---|
| **`skyflow`** | `import skyflow` | Privacy DB (v2.x) — vault CRUD, tokenize/detokenize, query, files, Detect, Connections | [skyvault/README.md](skyvault/README.md) |
| **`skyflow-flowvault-python`** | `import skyflow` | FlowVault (v1.x) — unary vault operations (insert, get, update, delete, detokenize) | [flowvault/README.md](flowvault/README.md) |

```bash
pip install skyflow                    # Privacy DB SDK
pip install skyflow-flowvault-python   # FlowVault SDK
```

> The two artifacts are versioned independently and **both install under the same top-level `skyflow`
> import**, so they cannot live in the same Python environment at once — install one per environment. A
> lower `skyflow-flowvault-python` version (1.x) does not mean it is behind `skyflow` (2.x); they are
> separate products.

## Repository layout

| Path | What it is |
|---|---|
| `common/` | Shared client, credentials, config, and error code — depended on by both SDKs, never published on its own. |
| `skyvault/` | The `skyflow` (Privacy DB / v2) SDK. |
| `flowvault/` | The `skyflow-flowvault-python` (FlowVault / v1) SDK. |
| `docs/` | Reference docs and the [v1 → v2 migration guide](docs/migrate_to_v2.md). |
| `CHANGELOG.md` | Release history. |

Each SDK ships runnable examples under its own `samples/` directory
([flowvault/samples/](flowvault/samples/), [skyvault/samples/](skyvault/samples/)).

## Documentation

- [Privacy DB SDK (`skyflow`) reference](skyvault/README.md)
- [FlowVault SDK (`skyflow-flowvault-python`) reference](flowvault/README.md)
- [v1 → v2 migration guide](docs/migrate_to_v2.md)
- [Skyflow docs](https://docs.skyflow.com/)

## Reporting a Vulnerability

If you discover a potential security issue, please email **security@skyflow.com** rather than opening a public GitHub issue.

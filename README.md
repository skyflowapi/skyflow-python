# Skyflow Python

This repository hosts Skyflow's Python SDKs for integrating Skyflow into a Python backend. It's a multi-package workspace with more than one published artifact — pick the package that matches what you need below.

[![CI](https://img.shields.io/static/v1?label=CI&message=passing&color=green?style=plastic&logo=github)](https://github.com/skyflowapi/skyflow-python/actions)
[![GitHub release](https://img.shields.io/github/v/release/skyflowapi/skyflow-python.svg)](https://github.com/skyflowapi/skyflow-python/releases)
[![License](https://img.shields.io/github/license/skyflowapi/skyflow-python)](https://github.com/skyflowapi/skyflow-python/blob/main/LICENSE)

## Which package do I want?

| Package | Artifact (PyPI) | README | Vault Type | Version line |
|---|---|---|---|---|
| **skyvault** | `skyflow` | [skyvault/README.md](skyvault/README.md) | SkyVault | 2.x |
| **flowvault** | `skyflow-flowvault-python` | [flowvault/README.md](flowvault/README.md) | FlowVault | 1.x |

`flowvault` shares auth/client setup with `skyvault` — both depend on the `common` module.

> **The two artifacts are versioned independently.** `flowvault` is a new SDK starting at `1.0.0`; its lower version number reflects a first release, not an older or lesser SDK than `skyvault` 2.x. Upgrade each on its own version line.

> **Install one per environment.** Both artifacts install under the same top-level `skyflow` import, so they cannot coexist in the same Python environment.

> Migrating from v1? See skyvault's **[Migration Guide](docs/migrate_to_v2.md)**. V1 is in maintenance mode and will reach End of Life on October 31, 2026.

## Repository layout

The workspace contains:

- `common/` — shared client, credentials, config, and error-handling code used by both `skyvault` and `flowvault`
- `skyvault/` — the `skyflow` SDK ([README](skyvault/README.md))
- `flowvault/` — the `skyflow-flowvault-python` SDK ([README](flowvault/README.md))

## Documentation

- [skyvault API Reference](docs/api_reference.md) — full list of request/response classes, enums, and service-account utilities
- [Migrate from v1 to v2](docs/migrate_to_v2.md)

## Reporting a Vulnerability

If you discover a potential security issue in this project, please reach out to us at **security@skyflow.com**. Please do not create public GitHub issues or Pull Requests, as malicious actors could potentially view them.

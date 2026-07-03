# SDK FlowDB Packaging Options: Same Package vs. Separate Package — SDK Installation & Import Comparison

| SDK | v2 (current) - PDB | v3 — same package (pinned)- FlowDB | separate package Name - FlowDB |
|---|---|---|---|
| **Node.js** | **Installation**: `npm install skyflow-node@2.0.0`<br>**Import:** `import { Skyflow } from 'skyflow-node';` | **Installation**: `npm install skyflow-node@3.0.0`<br>**Import:** `import { Skyflow } from 'skyflow-node';` | **Installation**: `npm install skyflow-flowdb-node@1.0.0`<br>**Import:** `import { Skyflow } from 'skyflow-flowdb-node';` |
| **Python** | **Installation**: `pip install "skyflow-python==2.0.0"`<br>**Import:** `from skyflow import Skyflow` | **Installation**: `pip install "skyflow-python==3.0.0"`<br>**Import:** `from skyflow import Skyflow` | **Installation**: `pip install "skyflow-flowdb-python==1.0.0"`<br>**Import:** `from skyflow_flowdb import Skyflow` |
| **Go** | **Installation**: `go get github.com/skyflowapi/skyflow-go/v2@v2.2.0`<br>**Import:** `import "github.com/skyflowapi/skyflow-go/v2/client"` | **Installation**: `go get github.com/skyflowapi/skyflow-go/v3@v3.0.0`<br>**Import:** `import "github.com/skyflowapi/skyflow-go/v3/client"` | **Installation**: `go get github.com/skyflowapi/skyflow-flowdb-go@v1.0.0`<br>**Import:** `import "github.com/skyflowapi/skyflow-flowdb-go/client"` |
| **Java** | **Installation**: `implementation 'com.skyflow:skyflow-java:2.0.0'`<br>**Import:** `import com.skyflow.Skyflow;` | **Installation**: `implementation 'com.skyflow:skyflow-java:3.0.0'`<br>**Import:** `import com.skyflow.Skyflow;` | **Installation**: `implementation 'com.skyflow:skyflow-flowdb-java:1.0.0'`<br>**Import:** `import com.skyflowflowdb.Skyflow;` |


> [!NOTE]
> **Separate package requires a separate GitHub repository for Go SDK.** A different SDK name (e.g. `skyflow-flowdb-go`) maps to a different source repository — it cannot be served from the existing `skyflow-go` repo without additional redirect infrastructure.


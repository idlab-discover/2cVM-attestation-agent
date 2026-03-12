# 2cVM Attestation Agent

The Attestation Agent is the central control component of the Two-Way Confidential VM (2cVM), a system for collaborative confidential computing between mutually distrustful parties.

It runs inside an AMD SEV-SNP confidential VM, enforces the policies defined in a Commitment Manifest, and orchestrates the full 2cVM lifecycle: locking the manifest, attesting the platform, admitting participant artifacts, composing and executing WebAssembly workloads, and returning authorized outputs.

> **This is a research prototype.** It has not been formally audited and is not intended for production use.

## How It Works

The agent exposes a REST API that drives three sequential stages:

1. **Lock** — One participant POSTs the negotiated Commitment Manifest to `/v1/lock`. The manifest is immutable from this point on.
2. **Attest & Submit** — Each participant calls `/v1/attestation` with a nonce to receive a hardware-signed SEV-SNP report and the signed Commitment Manifest. After verifying these, participants submit their code components and data via `/v1/application`. Submitted Wasm components are validated against their declared WIT/WASI imports before admission.
3. **Execute & Retrieve** — Once all artifacts are submitted, the agent automatically composes the Wasm components using `wac`, executes the composite binary with `wasmtime`, and makes outputs available at `/v1/application/result`. Each participant only receives outputs explicitly authorized for them in the manifest.

All runtime data (components, datasets, outputs) is stored in a volatile in-memory filesystem and destroyed when the VM shuts down.

## Requirements

- Python 3
- [wasmtime](https://wasmtime.dev)
- [wac CLI](https://github.com/bytecodealliance/wac)
- [wasm-tools](https://github.com/bytecodealliance/wasm-tools)
- [snpguest](https://github.com/virtee/snpguest) *(only on actual SEV-SNP hardware)*

Binary paths are configured in `agent/config.py`.

## Running Locally

For local development on non-SEV-SNP hardware, set `SEV_SNP_ENABLED = False` in `agent/config.py`. This mocks the platform attestation report.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn agent.main:app --reload
```

The API will be available at `http://localhost:8000`. With `DEV_MODE = True` (default), a `/v1/clear` endpoint is available to reset agent state between runs.

## Configuration

Key settings in `agent/config.py`:

| Setting | Default | Description |
|---|---|---|
| `SEV_SNP_ENABLED` | `False` | Set to `True` on real SEV-SNP hardware |
| `DEV_MODE` | `True` | Enables the `/v1/clear` reset endpoint |
| `AGENT_DIR` | `~/.attestation-agent` | Working directory for runtime state |
| `WASMTIME_BIN_FILE` | `~/.wasmtime/bin/wasmtime` | Path to wasmtime binary |
| `WAC_CLI_BIN_FILE` | `~/.cargo/bin/wac` | Path to wac binary |
| `SNP_GUEST_BIN_FILE` | `~/snpguest` | Path to snpguest binary |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/lock` | Lock the Commitment Manifest |
| `GET` | `/v1/attestation?nonce=<hex>` | Get SEV-SNP report + signed manifest |
| `POST` | `/v1/application` | Submit a component or dataset |
| `GET` | `/v1/application/result?participant=<id>` | Retrieve authorized outputs |
| `GET` | `/v1/status` | Current lock and submission state |
| `POST` | `/v1/clear` | Reset state *(dev mode only)* |

## Paper

Full architecture description, security model, and performance evaluation:

> J. Thijsman, M. Sebrechts, S. Lefever, F. De Turck, B. Volckaert, "Two-Way Confidential VMs (2cVM): Collaborative Confidential Computing for Mutually Distrustful Parties.

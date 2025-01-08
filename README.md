# SECODA-X Attestation Agent

## How to run locally?

0) Requirements:

>Installation directories can be adjusted in `config.py`

- [wasmtime](https://wasmtime.dev)
- [wac cli](https://github.com/bytecodealliance/wac)
- Python 3
- Permissions to create and write to `.attestation-agent` folder in your home directory

>For local debugging on a non SEV-SNP machine, set SEV_SNP_ENABLED to `False` in `config.py`. This will simulate getting the platform attestation report from the CPU.

1) Clone repo:

```
git clone git@github.com:jordithijsman/attestation-agent.git
cd attestation-agent
```

2) Set up venv and install requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3) Run webserver:
```bash
uvicorn agent.main:app --reload
```

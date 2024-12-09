# SECODA-X Attestation Agent


Clone repo:

```
git clone git@github.com:jordithijsman/attestation-agent.git
cd attestation-agent
```

Set up venv and install requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run webserver:
```bash
uvicorn app.main:app --reload
```

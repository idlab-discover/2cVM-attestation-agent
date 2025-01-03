import os

# General
SEV_SNP_enabled = False # Mock platform report for debuggin on non SEV-SNP systems
HOME_DIR = os.path.expanduser("~")
AGENT_DIR = os.path.join(HOME_DIR, ".attestation-agent")

# routes/application
WAMSTIME_BIN_FILE = os.path.join(HOME_DIR, ".wasmtime/bin/wasmtime")

# routes/attestation
KEY_FOLDER = os.path.join(AGENT_DIR, "keys")
SNP_GUEST_BIN_FILE = os.path.join(HOME_DIR, "snpguest")

# routes/lock
LOCK_FOLDER = os.path.join(AGENT_DIR, "lock")
LOCK_FILE = os.path.join(LOCK_FOLDER, "commitment-manifest.json")


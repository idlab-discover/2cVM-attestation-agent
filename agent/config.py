import os

# General
SEV_SNP_enabled = False  # Mock platform report for debuggin on non SEV-SNP systems
HOME_DIR = os.path.expanduser("~")
AGENT_DIR = os.path.join(HOME_DIR, ".attestation-agent")
API_VERSION = "V1"

# routes/application
APPLICATION_API_PATH = os.path.join("/", API_VERSION, "application")
WAMSTIME_BIN_FILE = os.path.join(HOME_DIR, ".wasmtime/bin/wasmtime")
WAC_CLI_BIN_FILE = os.path.join(HOME_DIR, ".cargo/bin/wac")
COMPONENT_FOLDER = os.path.join(AGENT_DIR, "component")
DATA_FOLDER = os.path.join(AGENT_DIR, "data")
WAC_FILE = os.path.join(COMPONENT_FOLDER, "composite.wac")
COMPOSITE_WASM_FILE = os.path.join(COMPONENT_FOLDER, "composite.wasm")
WASM_OUTPUT_DIR = os.path.join(AGENT_DIR, "output")

# routes/attestation
ATTESTATION_API_PATH = APPLICATION_API_PATH = os.path.join(
    "/", API_VERSION, "attestation")
SNP_GUEST_BIN_FILE = os.path.join(HOME_DIR, "snpguest")
KEY_FOLDER = os.path.join(AGENT_DIR, "keys")
PRIVATE_KEY_FILE = os.path.join(KEY_FOLDER, "private_key.pem")
PUBLIC_KEY_FILE = os.path.join(KEY_FOLDER, "public_key.pem")

# routes/lock
LOCK_API_PATH = APPLICATION_API_PATH = os.path.join("/", API_VERSION, "lock")
LOCK_FOLDER = os.path.join(AGENT_DIR, "lock")
LOCK_FILE = os.path.join(LOCK_FOLDER, "commitment-manifest.json")

# routes/status
STATUS_API_PATH = APPLICATION_API_PATH = os.path.join(
    "/", API_VERSION, "status")

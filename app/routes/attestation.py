import base64
import subprocess
import os
from fastapi import APIRouter, HTTPException, Response, Query
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/v1/attestation", tags=["Application"])

HOME_DIR = os.path.expanduser("~")
BIN_FILE = "snpguest"

# TODO:
# Check if keypair exists
# Generate asym keypair
# Concat and hash pub key and nonce
# Request attestation report (include user and hash of pub key)
# Check if TEE is locked, get manifest and sign lock with key
# Send both reports + pub key

@router.get("/")
async def attestation(hex_nonce: str = Query(...)):
    try:
        binary_nonce = bytes.fromhex(hex_nonce)

        # TODO: generate keypair and write to 'disk'
        tee_pub_key = base64.b64encode(b"this is a public key").decode("utf-8")
        tee_priv_key = base64.b64encode(b"this is a private key").decode("utf-8")

        report_path = generate_platform_report(hex_nonce, tee_pub_key)

        # TODO: Read binary report, and encode it to b64
        platform_attestation = base64.b64encode(b"this is an attestation report").decode("utf-8")

        # TODO: Read commitment manifest file into this variable
        commitment_manifest = {}

        # TODO: Sign manifest with tee_priv_key
        commitment_manifest_signature = base64.b64encode(b"this is a signature").decode("utf-8")

        full_attestation = {
            "platform_attestation": platform_attestation,
            "commitment_attestation": {
                "commitment_manifest": commitment_manifest,
                "commitment_manifest_signature": commitment_manifest_signature},
            "tee_pub_key" : tee_pub_key
        }

        # TODO: clean up report file

        return JSONResponse(content=full_attestation)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid nonce: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

def generate_platform_report(binary_nonce, tee_pub_key):
    

    # TODO: Append nonce to tee_pub_key and SHA-256 the result. Pad to 64 bytes with 0's
    # TODO: Write result to nonce file

    # TODO: Check if binary is installed
    bin_path = os.path.join(HOME_DIR, BIN_FILE)

    # TODO: Files need unique names, to prevent mixing up nonces: generate unique names
    nonce_file = "abc" + "nonce.bin"
    report_file = "xyz" + "report.bin"

    # Note: for prod, this app should be rewritten in Rust and just use the snpguest functions directly, avoiding all these 'disk' writes.
    result = subprocess.run([bin_path, str("report"), str(os.path.join(HOME_DIR, report_file)), str(os.path.join(HOME_DIR, nonce_file))], capture_output=True, text=True)

    # TODO: Clean up nonce file

    if result.returncode == 0:
        print(f"Output: {result.stdout.strip()}")
    else:
        print(f"Error: {result.stderr.strip()}")
    
    return os.path.join(HOME_DIR, report_file)
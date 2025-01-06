import base64
import subprocess
import os
import hashlib
import getpass

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

import agent.config as config
from agent.models.commitment_manifest import CommitmentManifest, ThreadSafeCommitmentManifest

router = APIRouter(prefix=config.ATTESTATION_API_PATH, tags=["Application"])


@router.get("/")
async def attestation(request: Request, hex_nonce: str = Query(...)):
    try:
        # Check if key pair already exist, else generate
        if not (os.path.exists(config.PRIVATE_KEY_FILE) or os.path.exists(config.PUBLIC_KEY_FILE)):
            tee_priv_key, tee_pub_key = generate_key_pair()
        else:
            tee_priv_key, tee_pub_key = read_key_pair()

        tee_pub_key_b64 = base64.b64encode(
            tee_pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo)
        ).decode("utf-8")

        # Mock platform attestation for dev (set in config.py)
        if not config.SEV_SNP_enabled:
            platform_attestation = "abcdef"
        else:
            report_path = generate_platform_report(hex_nonce, tee_pub_key)

            with open(report_path, 'rb') as f:
                platform_attestation = base64.b64encode(
                    f.read()).decode("utf-8")

        # Verify that platform is locked, if not -> return empty
        commitment_manifest: ThreadSafeCommitmentManifest = getattr(
            request.app.state, 'commitment_manifest', None)
        if commitment_manifest != None and commitment_manifest.data != None:

            commitment_manifest_data: CommitmentManifest = commitment_manifest.data
            commitment_manifest_signature = tee_priv_key.sign(
                commitment_manifest.model_dump_json().encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
        else:
            commitment_manifest_data = None
            commitment_manifest_signature = None

        full_attestation = {
            "platform_attestation": platform_attestation,
            "commitment_attestation": {
                "commitment_manifest": commitment_manifest_data.model_dump() if commitment_manifest_data else None,
                "commitment_manifest_signature": base64.b64encode(commitment_manifest_signature).decode("utf-8") if commitment_manifest_signature else None
            },
            "tee_pub_key": tee_pub_key_b64
        }

        if config.SEV_SNP_enabled:
            os.remove(report_path)

        return JSONResponse(content=full_attestation)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid nonce: {e}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


def generate_platform_report(hex_nonce, tee_pub_key):

    # Generate user_data field for report
    binary_nonce = bytes.fromhex(hex_nonce)
    nonce_hash = hashlib.sha256(binary_nonce).digest()

    public_key_hash = hashlib.sha256(
        tee_pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
    ).digest()

    user_data = nonce_hash + public_key_hash

    user_data_file_path = os.path.join(
        config.HOME_DIR, hex_nonce + "user_data.bin")

    with open(user_data_file_path, 'wb') as f:
        f.write(user_data)

    # Check if snpguest binary is installed
    if not os.path.exists(config.SNP_GUEST_BIN_FILE):
        raise Exception

    report_file_path = os.path.join(config.AGENT_DIR, hex_nonce + "report.bin")

    # Note: for prod, this app should be rewritten in Rust and just use the snpguest functions directly, avoiding all these 'disk' writes.
    # These files are actually written to a virtual fs in encrypted memory, no nothing leaks to host.
    result = subprocess.run(["/usr/bin/sudo", config.SNP_GUEST_BIN_FILE, "report",
                             report_file_path,
                             user_data_file_path],
                            capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception

    # This is ugly, if this is implemented in rust with direct integration into snpguest this wouldn't be necessary.
    result = subprocess.run(["/usr/bin/sudo", "/usr/bin/chown",
                             getpass.getuser(),
                             str(report_file_path), str(user_data_file_path)],
                            capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception

    # Clean up
    os.remove(user_data_file_path)

    return report_file_path


def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    if not os.path.exists(config.KEY_FOLDER):
        os.mkdir(config.KEY_FOLDER)

    # Write keys to file
    # These files are actually written to a virtual fs in encrypted memory, no nothing leaks to host.
    with open(config.PRIVATE_KEY_FILE, "wb") as private_file:
        private_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    with open(config.PUBLIC_KEY_FILE, "wb") as public_file:
        public_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    return private_key, public_key


def read_key_pair():
    with open(config.PUBLIC_KEY_FILE, "rb") as pub_file:
        public_key = serialization.load_pem_public_key(
            pub_file.read()
        )

    if isinstance(public_key, rsa.RSAPublicKey):
        print("Public key successfully loaded as RSAPublicKey.")
    else:
        raise ValueError("The public key is not of type RSAPublicKey.")

    with open(config.PRIVATE_KEY_FILE, "rb") as priv_file:
        private_key = serialization.load_pem_private_key(
            priv_file.read(),
            password=None
        )

    if isinstance(private_key, rsa.RSAPrivateKey):
        print("Private key successfully loaded as RSAPrivateKey.")
    else:
        raise ValueError("The private key is not of type RSAPrivateKey.")

    return private_key, public_key

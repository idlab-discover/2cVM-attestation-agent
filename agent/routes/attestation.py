import base64
import subprocess
import os
import traceback
import hashlib
import getpass

from fastapi import APIRouter, HTTPException, Query ,Request
from fastapi.responses import JSONResponse

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes


from agent.models.commitment_manifest import CommitmentManifest
from agent.config import SEV_SNP_enabled

router = APIRouter(prefix="/v1/attestation", tags=["Application"])

HOME_DIR = os.path.join(os.path.expanduser("~"), ".attestation-agent")
KEY_FOLDER = os.path.join(HOME_DIR, "keys")

BIN_DIR = os.path.expanduser("~")
BIN_FILE = "snpguest"

# TODO:
# Check if keypair exists
# Generate asym keypair
# Concat pub key and hash of nonce
# Request attestation report (include user and hash of pub key)
# Check if TEE is locked, get manifest and sign lock with key
# Send both reports + pub key

@router.get("/")
async def attestation(request: Request, hex_nonce: str = Query(...)):
    try:
        binary_nonce = bytes.fromhex(hex_nonce)
        
        if not (os.path.exists(os.path.join(HOME_DIR + KEY_FOLDER, "private_key.pem")) or os.path.exists(os.path.join(HOME_DIR + KEY_FOLDER, "public_key.pem"))):
            tee_priv_key, tee_pub_key = generate_key_pair()
        else:
            tee_priv_key, tee_pub_key = read_key_pair()

        # TODO: generate keypair and write to 'disk'
        tee_pub_key_b64 = base64.b64encode(
            tee_pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo)
            ).decode("utf-8")

        if not SEV_SNP_enabled:
            platform_attestation = "abcdef"
        else:
            report_path = generate_platform_report(hex_nonce, tee_pub_key)

            # TODO: Read binary report, and encode it to b64
            
            with open(report_path, 'rb') as f:
                platform_attestation = base64.b64encode(f.read()).decode("utf-8")
        
        # Verify that platform is locked, if not -> return empty 
        if hasattr(request.app.state, 'commitment_manifest'):
            commitment_manifest: CommitmentManifest = request.app.state.commitment_manifest
            commitment_manifest_signature = tee_priv_key.sign(
                commitment_manifest.model_dump_json().encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
        else:
            commitment_manifest = None
            commitment_manifest_signature = None
            
        full_attestation = {
            "platform_attestation": platform_attestation,
            "commitment_attestation": {
                "commitment_manifest": commitment_manifest.model_dump() if commitment_manifest else None,
                "commitment_manifest_signature": base64.b64encode(commitment_manifest_signature).decode("utf-8") if commitment_manifest_signature else None
            },
            "tee_pub_key": tee_pub_key_b64
        }


        if SEV_SNP_enabled:
            os.remove(report_path)

        return JSONResponse(content=full_attestation)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid nonce: {e}")
    except Exception as e:
        traceback.print_exc()
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
    
    user_data_file_path = os.path.join(HOME_DIR, hex_nonce + "user_data.bin")
    
    with open(user_data_file_path, 'wb') as f:
        f.write(user_data)

    # Check if snpguest binary is installed
    if not os.path.exists(os.path.join(BIN_DIR, BIN_FILE)):
        raise Exception

    report_file_path = os.path.join(HOME_DIR, hex_nonce + "report.bin")

    # Note: for prod, this app should be rewritten in Rust and just use the snpguest functions directly, avoiding all these 'disk' writes.
    result = subprocess.run(["/usr/bin/sudo", os.path.join(BIN_DIR, BIN_FILE), str("report"), str(report_file_path), str(user_data_file_path)], 
                            capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception
    
    # This is ugly, if this is implemented in rust with direct integration into snpguest this wouldn't be necessary.
    result = subprocess.run(["/usr/bin/sudo", "/usr/bin/chown", getpass.getuser(), str(report_file_path), str(user_data_file_path)], 
                            capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception
    
    os.remove(user_data_file_path)    
    
    return report_file_path
    
def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,  
        key_size=2048         
    )
    public_key = private_key.public_key()
    
    if not os.path.exists(KEY_FOLDER):
        os.mkdir(KEY_FOLDER)
    
    with open(os.path.join(KEY_FOLDER, "private_key.pem"), "wb") as private_file:
        private_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    with open(os.path.join(KEY_FOLDER, "public_key.pem"), "wb") as public_file:
        public_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    return private_key, public_key

def read_key_pair():
    with open(os.path.join(KEY_FOLDER, "public_key.pem"), "rb") as pub_file:
        public_key = serialization.load_pem_public_key(
            pub_file.read()
        )

    if isinstance(public_key, rsa.RSAPublicKey):
        print("Public key successfully loaded as RSAPublicKey.")
    else:
        raise ValueError("The public key is not of type RSAPublicKey.")

    with open(os.path.join(KEY_FOLDER, "private_key.pem"), "rb") as priv_file:
        private_key = serialization.load_pem_private_key(
            priv_file.read(),
            password=None
        )

    if isinstance(private_key, rsa.RSAPrivateKey):
        print("Private key successfully loaded as RSAPrivateKey.")
    else:
        raise ValueError("The private key is not of type RSAPrivateKey.")
    
    return private_key, public_key

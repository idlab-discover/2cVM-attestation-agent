import requests
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import json

api_url = 'http://localhost:8000/v1/attestation?hex_nonce=FFFFFF'
response = requests.get(api_url)

if response.status_code != 200:
    print(f"Failed to fetch data from API: {response.status_code}")
    exit()

data = response.json()

platform_attestation = base64.b64decode(data["platform_attestation"]).decode('utf-8')
commitment_manifest = data["commitment_attestation"]["commitment_manifest"]
commitment_manifest_signature = base64.b64decode(data["commitment_attestation"]["commitment_manifest_signature"])

public_key_pem = base64.b64decode(data["tee_pub_key"])

try:
    public_key = serialization.load_pem_public_key(public_key_pem)
except ValueError as e:
    print(f"Failed to load public key: {e}")
    exit()

commitment_manifest_json = json.dumps(commitment_manifest, separators=(',', ':'))

try:
    public_key.verify(
        commitment_manifest_signature,
        commitment_manifest_json.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("Signature is valid")
except InvalidSignature:
    print("Signature verification failed")
except Exception as e:
    print(f"Error verifying signature: {e}")

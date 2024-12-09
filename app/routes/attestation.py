import base64
from fastapi import APIRouter, HTTPException, Response, Query


router = APIRouter(prefix="/v1/attestation", tags=["Application"])

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

        platform_attestation = base64.b64encode(b"this is an attestation report").decode("utf-8")
        tee_pub_key = base64.b64encode(b"this is a public key").decode("utf-8")

        commitment_manifest = {}

        commitment_manifest_signature = base64.b64encode(b"this is a signature").decode("utf-8")

        full_attestation = {
            "platform_attestation": platform_attestation,
            "commitment_attestation": {
                "commitment_manifest": commitment_manifest,
                "commitment_manifest_signature": commitment_manifest_signature},
            "tee_pub_key" : tee_pub_key
        }

        return Response(content=full_attestation, media_type="application/json")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid nonce: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
import json
import os
import traceback

from fastapi import APIRouter, HTTPException, Request, Response

from agent.models.commitment_manifest import CommitmentManifest, ThreadSafeCommitmentManifest

router = APIRouter(prefix="/v1/lock", tags=["Lock"])

# Define folders for manifest
HOME_DIR = os.path.join(os.path.expanduser("~"), ".attestation-agent")
LOCK_FOLDER = os.path.join(HOME_DIR, "lock")
LOCK_FILE = "commitment-manifest.json"

@router.post("/")
async def lock(request: Request):
    data = await request.json()
    try:

        # Check if TEE is locked already
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(request.app.state, 'commitment_manifest', None)
        if thread_safe_commitment_manifest != None and thread_safe_commitment_manifest.data != None:
            raise HTTPException(status_code=400, detail="TEE is already locked")

        # Not locked, parse JSON
        data = await request.json()

        # If folder does not exist, create it
        if not os.path.exists(LOCK_FOLDER):
            os.makedirs(LOCK_FOLDER)
            print(f"Folder '{LOCK_FOLDER}' created.")

        file_path = os.path.join(LOCK_FOLDER, LOCK_FILE)

        # Note: writing is fine here as this is a tmpfs mounted from memory. 
        # Nothing is ever really written to disk and thus everything is encrypted.
        with open(file_path, 'w') as file:
            json.dump(data, file)
            # Save CM as state so other enpoints don't need to parse json file every time
            thread_safe_commitment_manifest = ThreadSafeCommitmentManifest()
            await thread_safe_commitment_manifest.lock(**data)
            request.app.state.commitment_manifest = thread_safe_commitment_manifest
            print("Commitment manifest has been locked.")
            
        return Response(status_code=200)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
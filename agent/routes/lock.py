import json
import os
import traceback

from fastapi import APIRouter, HTTPException, Request, Response

import agent.config as config

router = APIRouter(prefix="/v1/lock", tags=["Lock"])

# This endpoint locks the TEE to a commitment manifest
@router.post("/")
async def lock(request: Request):
    data = await request.json()
    try:

        # Check if TEE is locked already
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(request.app.state, 'commitment_manifest', None)
        if thread_safe_commitment_manifest != None and thread_safe_commitment_manifest.data != None:
            raise HTTPException(status_code=400, detail="TEE is already locked")

        if not os.path.exists(config.LOCK_FOLDER):
            os.makedirs(config.LOCK_FOLDER)
        
        data = await request.json()

        # If folder does not exist, create it
        if not os.path.exists(LOCK_FOLDER):
            os.makedirs(LOCK_FOLDER)
            print(f"Folder '{LOCK_FOLDER}' created.")

        file_path = os.path.join(LOCK_FOLDER, LOCK_FILE)

        # Note: writing is fine here as this is a tmpfs mounted from memory. 
        with open(config.LOCK_FILE, 'w') as file:
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
import json
import os
from fastapi import APIRouter, HTTPException, Request, Response
from agent.models.commitment_manifest import CommitmentManifest

router = APIRouter(prefix="/v1/lock", tags=["Lock"])

# Define folders for manifest
HOME_DIR = os.path.expanduser("~")
LOCK_FOLDER = os.path.join(HOME_DIR, ".lock")
LOCK_FILE = "commitment-manifest.json"

@router.post("/")
async def lock(request: Request):
    data = await request.json()
    try:
        # Check if TEE is locked to avoid parsing JSON
        if os.path.exists(LOCK_FOLDER) and os.listdir(LOCK_FOLDER):
            raise HTTPException(status_code=400, detail="TEE is already locked")
        else:
            print(f"Folder {LOCK_FOLDER} does not exist or is empty.")

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
            request.app.state.commitment_manifest = CommitmentManifest(**data)
            print("Commitment manifest has been locked.")
            
        return Response(status_code=200)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
import json
import os
import traceback

from fastapi import APIRouter, HTTPException, Request, Response

import agent.config as config
from agent.models.commitment_manifest import ThreadSafeCommitmentManifest
from agent.models.party_submission_state import ThreadSafePartySubmissionState

router = APIRouter(prefix="/v1/lock", tags=["Lock"])

# This endpoint locks the TEE to a commitment manifest
@router.post("/")
async def lock(request: Request):
    data = await request.json()
    try:
        # Check if TEE is locked already
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(request.app.state, 'commitment_manifest', None)
        thread_safe_party_submission_state: ThreadSafePartySubmissionState = getattr(request.app.state, 'party_submission_state', None)
        
        if thread_safe_commitment_manifest != None and thread_safe_commitment_manifest.commitment_data != None:
            raise HTTPException(status_code=400, detail="TEE is already locked")

        if not os.path.exists(config.LOCK_FOLDER):
            os.makedirs(config.LOCK_FOLDER)
        
        data = await request.json()

        # Note: writing is fine here as this is a tmpfs mounted from memory. 
        with open(config.LOCK_FILE, 'w') as file:
            json.dump(data, file)
            
        # Save CM as state so other enpoints don't need to parse json file every time
        thread_safe_commitment_manifest = ThreadSafeCommitmentManifest()
        await thread_safe_commitment_manifest.lock(**data)
        request.app.state.commitment_manifest = thread_safe_commitment_manifest
        
        party_data = parse_party_submission_state(thread_safe_commitment_manifest)
        await thread_safe_party_submission_state.lock(**party_data)
            
        return Response(status_code=200)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def parse_party_submission_state(commitment_manifest: ThreadSafeCommitmentManifest):
    submission_state = {}
    for component in commitment_manifest.commitment_data.components:
        submission_state[component.name] = False
        
    for data in commitment_manifest.commitment_data.data:
        submission_state[data.name] = False
        
    return submission_state
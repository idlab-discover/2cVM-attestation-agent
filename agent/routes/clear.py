import os
import traceback
from fastapi import APIRouter, HTTPException, Request

from agent import config
from agent.models.commitment_manifest import ThreadSafeCommitmentManifest
from agent.models.party_submission_state import ThreadSafePartySubmissionState


router = APIRouter(prefix=config.CLEAR_API_PATH, tags=["Clear"])

# Dev endpoint to reset all entries
@router.post("/")
async def lock(request: Request):
    try:
        for root, dirs, files in os.walk(config.AGENT_DIR, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        
        request.app.state.party_submission_state = ThreadSafePartySubmissionState()
        request.app.state.commitment_manifest = ThreadSafeCommitmentManifest()
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
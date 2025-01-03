import json
import os
import subprocess

from fastapi import APIRouter, HTTPException, Request, Response, Query

from agent.models.commitment_manifest import CommitmentManifest
from agent.models.verifiable_credential import VerifiableCredential

router = APIRouter(prefix="/v1/application", tags=["Application"])

@router.post("/")
async def application(request: Request):
    try:
        data = await request.json()

        #Check if commitment manifest exists
        if not hasattr(request.app.state, 'commitment_manifest'):
            # TODO: What error should this throw? And what HTTP response should this trigger?
            raise Exception()
        
        commitment_manifest: CommitmentManifest = request.app.state.commitment_manifest
        
        data = await request.json()
        
        verifiable_credential = VerifiableCredential(**data)

        # TODO: Check if VC is expected, if yes: store to file
        
        # Note: We can only mount folders, not individual files -> Store VC to file in folder with name of component that should receive it.
        # A production implementation should pass these files in a different way (using Rust)
        
        # TODO: Check if all components and data present -> yes? compose and run
        #bin_path = os.path.join(HOME_DIR, BIN_FILE)
        #result = subprocess.run([bin_path, str("pass dir here")], capture_output=True, text=True)

        return Response(status_code=200)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# TODO:
# Verify party identity
# Check if user with user id should get result (as defined in lock)
# Check if there is a result
# If yes to all, provide result. (possibly sign with key for provenance?)

@router.get("/result")
async def result(user_identification: str = Query(...)):
    try:

        return Response(status_code=200, content="{result : something}", media_type="application/json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def compose_wasm():
    return True

def run_wasm():
    return True    

def verify_identity():
    return True
import json
import os
import subprocess
import traceback
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response, Query

import agent.config as config
from agent.models.commitment_manifest import Component, Data, Output, ThreadSafeCommitmentManifest
from agent.models.party_submission_state import ThreadSafePartySubmissionState
from agent.models.verifiable_credential import VerifiableCredential


router = APIRouter(prefix="/v1/application", tags=["Application"])

@router.post("/")
async def application(request: Request):
    try:
        # Check if commitment manifest exists and is correctly locked
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(request.app.state, 'commitment_manifest', None)
        thread_safe_party_submission_state: ThreadSafePartySubmissionState = getattr(request.app.state, 'party_submission_state', None)
        if (thread_safe_commitment_manifest == None or thread_safe_commitment_manifest.commitment_data == None or
            thread_safe_party_submission_state == None or thread_safe_party_submission_state.data == None):
            raise HTTPException(status_code=400, detail="No commitment manifest locked")
        
        # Parse request json as VC
        data = await request.json()
        verifiable_credential = VerifiableCredential(**data)
        VC_manifest_id: str = verifiable_credential.credentialSubject.manifest.id
        VC_subject_id: str = verifiable_credential.credentialSubject.id
        VC_manifest_type: str = verifiable_credential.credentialSubject.manifest.type
        
        # Verify type and look up in commitment manifest
        if not is_verifiable_credential_valid(verifiable_credential, thread_safe_commitment_manifest):
            raise HTTPException(status_code=400, detail="Unexpected type in VC")

        # Create dir if not present
        dir = os.path.join(config.AGENT_DIR, VC_manifest_type)
        print(dir)
        if not os.path.exists(dir):
            os.makedirs(dir)
        # Write data or component to file
        with open(os.path.join(dir, VC_manifest_id), 'w') as file:
            json.dump(verifiable_credential.credentialSubject.manifest.body, file)        

        # Check if TEE is properly locked
        
        if thread_safe_party_submission_state == None or thread_safe_party_submission_state.data == None:
            raise HTTPException(status_code=400, detail="TEE not locked")
        
        await thread_safe_party_submission_state.mark_data_as_submitted(VC_manifest_id)
        
        return Response(status_code=200)
        
        if thread_safe_party_submission_state.all_data_present():
            compose_wasm()
            run_wasm()

        return Response(status_code=200)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/result")
async def result(request: Request, user_identification: str = Query(...)):
    try:
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(request.app.state, 'commitment_manifest', None)
        if thread_safe_commitment_manifest != None and thread_safe_commitment_manifest.data != None:
            raise HTTPException(status_code=400, detail="No commitment manifest locked")
        
        output_permissions: List[Output] = thread_safe_commitment_manifest.commitment_data.permissions
        
        for output in output_permissions:
            if output.participant == user_identification:
                print("lookup output file and include it")
        
        return Response(status_code=200, content="{result : something}", media_type="application/json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def compose_wasm(thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    # TODO: write wac to file (this will not be necessary when rewriting in Rust)
    # Create composite .wasm using CLI
    raise HTTPException(status_code=400, detail="Failed to compose, invalid composition")

def run_wasm():
    # Currently files all files are accessible to all parties
    
    # (TODO: store process in memory so status can show process status)
    
    # TODO: call wasmtime command with composite .wasm and dir with data
    return True    

def verify_identity():
    return True


# Check if data or component in VC is exepcted according to CM
def is_verifiable_credential_valid(verifiable_credential: VerifiableCredential, thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    # TODO: add proper identity validation of party (not for demonstrator)
    
    VC_subject_id = verifiable_credential.credentialSubject.id
    VC_type: str = verifiable_credential.credentialSubject.manifest.type
    VC_manifest_id: str = verifiable_credential.credentialSubject.manifest.id
    
    CM_data: List[Data] = thread_safe_commitment_manifest.commitment_data.data
    CM_components: List[Component] = thread_safe_commitment_manifest.commitment_data.components
    
    if VC_type == "data":
        for data in CM_data:
            if data.name == VC_manifest_id and data.participant == VC_subject_id:
                print("valid")
                return True
            
    elif VC_type == "component":
        for component in CM_components:
            if component.name == VC_manifest_id and component.participant == VC_subject_id:
                print("valid")
                return True
    else: 
        return False
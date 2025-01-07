import base64
import time 
import json
import os
import subprocess
import traceback
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response, Query

import agent.config as config
from agent.models.commitment_manifest import Component, Data, Output, Permission, ThreadSafeCommitmentManifest
from agent.models.party_submission_state import ThreadSafePartySubmissionState
from agent.models.verifiable_credential import VerifiableCredential


router = APIRouter(prefix=config.APPLICATION_API_PATH, tags=["Application"])


@router.post("/")
async def application(request: Request):
    try:
        # Check if commitment manifest exists and is correctly locked
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(
            request.app.state, 'commitment_manifest', None)
        thread_safe_party_submission_state: ThreadSafePartySubmissionState = getattr(
            request.app.state, 'party_submission_state', None)
        if (thread_safe_commitment_manifest == None or thread_safe_commitment_manifest.commitment_data == None or
                thread_safe_party_submission_state == None or thread_safe_party_submission_state.data == None):
            raise HTTPException(
                status_code=400, detail="No commitment manifest locked")

        # Parse request json as VC
        data = await request.json()
        verifiable_credential = VerifiableCredential(**data)
        VC_manifest_id: str = verifiable_credential.credentialSubject.manifest.id
        VC_participant: str = get_participant_for_did(verifiable_credential.credentialSubject.id, thread_safe_commitment_manifest)
        VC_manifest_content_type: str = verifiable_credential.credentialSubject.manifest.type

        # Verify type and look up in commitment manifest
        if not is_verifiable_credential_valid(verifiable_credential, thread_safe_commitment_manifest):
            raise HTTPException(
                status_code=400, detail="Unexpected type in VC")

        if VC_manifest_content_type == "component":
            # Note: components are expected in deps/namespace/component.wasm relative to .wac file.
            # namespace = partner name, component.wasm = file name
            dir = os.path.join(config.COMPONENT_FOLDER, "deps", VC_participant)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(os.path.join(dir, VC_manifest_id + ".wasm"), 'wb') as file:
                file.write(base64.b64decode(
                    verifiable_credential.credentialSubject.manifest.body))

        elif VC_manifest_content_type == "data":
            dir = os.path.join(config.DATA_FOLDER, VC_participant)
            if not os.path.exists(dir):
                os.makedirs(dir)
            # Write data or component to file
            with open(os.path.join(dir, VC_manifest_id), 'w') as file:
                json.dump(
                    verifiable_credential.credentialSubject.manifest.body, file)

        else:
            raise Exception

        # Check if TEE is properly locked
        if thread_safe_party_submission_state == None or thread_safe_party_submission_state.data == None:
            raise HTTPException(status_code=400, detail="TEE not locked")

        await thread_safe_party_submission_state.mark_data_as_submitted(VC_manifest_id)

        if await thread_safe_party_submission_state.all_data_present():
            compose_wasm(thread_safe_commitment_manifest)
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
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(
            request.app.state, 'commitment_manifest', None)
        if thread_safe_commitment_manifest == None or thread_safe_commitment_manifest.commitment_data == None:
            raise HTTPException(
                status_code=400, detail="No commitment manifest locked")

        thread_safe_commitment_manifest.commitment_data.permissions
        component_permission: List[Permission] = thread_safe_commitment_manifest.commitment_data.permissions

        return_data = {}
        for component in component_permission:
            for output_permission in component.output:
                if output_permission.participant == user_identification:
                    output_file_path = os.path.join(
                        config.WASM_OUTPUT_DIR, output_permission.name)
                    # If text, return text
                    if (is_text(output_file_path)):
                        with open(output_file_path, 'r') as file:
                            return_data[output_permission.name] = file.read()
                    # If not text, return b64 encoded binary
                    else:
                        with open(output_file_path, "rb") as file:
                            return_data[output_permission.name] = base64.b64encode(
                                file.read()).decode('utf-8')

        return Response(status_code=200, content=json.dumps(return_data), media_type="application/json")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")


def compose_wasm(thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    # Write WAC from commitment manifest to file in components folder
    with open(config.WAC_FILE, 'w') as file:
        file.write(json.loads(json.dumps(thread_safe_commitment_manifest.commitment_data.composition)))

    print(config.WAC_CLI_BIN_FILE)
    # Check if WAC CLI tool installed
    if not os.path.exists(config.WAC_CLI_BIN_FILE):
        raise Exception
    
    # Run WAC CLI to create composite .wasm
    result = subprocess.run([str(config.WAC_CLI_BIN_FILE), "compose",
                             "--deps-dir", str(os.path.join(config.COMPONENT_FOLDER, "deps")),
                             "-o", str(config.COMPOSITE_WASM_FILE),
                             str(config.WAC_FILE)],
                            capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception


def run_wasm():
    # (TODO: maybe store process as state to check on progress later?)

    # Check if wasmtime is installed
    if not os.path.exists(config.WAMSTIME_BIN_FILE):
        raise Exception
    
    if not os.path.exists(config.WASM_OUTPUT_DIR):
        os.mkdir(config.WASM_OUTPUT_DIR)

    # Run composite WASM binary
    process = subprocess.Popen(
        # Currently give r/w access to all data files and output folers, more granular control requires modifying wasmtime (future work)
        [config.WAMSTIME_BIN_FILE,
         "--dir", config.DATA_FOLDER + "::/data",
         "--dir", config.WASM_OUTPUT_DIR + "::/output",
         config.COMPOSITE_WASM_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True  # Detach subprocess so it keeps running, even if this code crashes
    )

def is_verifiable_credential_valid(verifiable_credential: VerifiableCredential, thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    # (TODO: add proper identity validation of party (not for demonstrator))

    VC_subject_did = verifiable_credential.credentialSubject.id
    VC_type: str = verifiable_credential.credentialSubject.manifest.type
    VC_manifest_id: str = verifiable_credential.credentialSubject.manifest.id

    CM_data: List[Data] = thread_safe_commitment_manifest.commitment_data.data
    CM_components: List[Component] = thread_safe_commitment_manifest.commitment_data.components

    if VC_type == "data":
        for data in CM_data:
            if data.name == VC_manifest_id and get_did_for_participant(data.participant, thread_safe_commitment_manifest) == VC_subject_did:
                return True

    elif VC_type == "component":
        for component in CM_components:
            if component.name == VC_manifest_id and get_did_for_participant(component.participant, thread_safe_commitment_manifest) == VC_subject_did:
                return True
    else:
        return False

def get_did_for_participant(participant_name: str, thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    for participant in thread_safe_commitment_manifest.commitment_data.participants:
        if participant.name == participant_name:
            return participant.DID
        
def get_participant_for_did(did: str, thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    for participant in thread_safe_commitment_manifest.commitment_data.participants:
        if participant.DID == did:
            return participant.name

def is_text(file_path: str):
    try:
        with open(file_path, 'r') as file:
            file.read()
        return True
    except:
        return False

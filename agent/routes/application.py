import base64
import json
import os
import subprocess
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response, Query

import agent.config as config
from agent.models.commitment_manifest import Component, Data, Output, ThreadSafeCommitmentManifest
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
        VC_subject_id: str = verifiable_credential.credentialSubject.id
        VC_manifest_type: str = verifiable_credential.credentialSubject.manifest.type

        # Verify type and look up in commitment manifest
        if not is_verifiable_credential_valid(verifiable_credential, thread_safe_commitment_manifest):
            raise HTTPException(
                status_code=400, detail="Unexpected type in VC")

        if VC_manifest_type == "component":
            # Note: components are expected in deps/namespace/component.wasm relative to .wac file.
            # namespace = partner name, component.wasm = file name
            dir = os.path.join(config.COMPONENT_FOLDER, "deps", VC_subject_id)
        elif VC_manifest_type == "data":
            dir = os.path.join(config.DATA_FOLDER, VC_subject_id)
        else:
            raise Exception

        # Create dir if not present
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Write data or component to file
        with open(os.path.join(dir, VC_manifest_id), 'w') as file:
            json.dump(verifiable_credential.credentialSubject.manifest.body, file)

        # Check if TEE is properly locked
        if thread_safe_party_submission_state == None or thread_safe_party_submission_state.data == None:
            raise HTTPException(status_code=400, detail="TEE not locked")

        await thread_safe_party_submission_state.mark_data_as_submitted(VC_manifest_id)

        if thread_safe_party_submission_state.all_data_present():
            compose_wasm(thread_safe_commitment_manifest)
            run_wasm()

        return Response(status_code=200)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/result")
async def result(request: Request, user_identification: str = Query(...)):
    try:
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(
            request.app.state, 'commitment_manifest', None)
        if thread_safe_commitment_manifest != None and thread_safe_commitment_manifest.data != None:
            raise HTTPException(
                status_code=400, detail="No commitment manifest locked")

        output_permissions: List[Output] = thread_safe_commitment_manifest.commitment_data.permissions

        return_data = {}
        for output in output_permissions:
            if output.participant == user_identification:
                output_file_path = os.path.join(
                    config.WASM_OUTPUT_DIR, output.name)
                # If text, return text
                if (is_text(output_file_path)):
                    with open(output_file_path, 'r') as file:
                        return_data[output.name] = file.read()
                # If not text, return b64 encoded binary
                else:
                    with open(output_file_path, "rb") as file:
                        return_data[output.name] = base64.b64encode(
                            file.read()).decode('utf-8')

        return Response(status_code=200, content=return_data, media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


def compose_wasm(thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Write WAC from commitment manifest to file in components folder
    with open(config.WAC_FILE, 'w') as file:
        json.dump(thread_safe_commitment_manifest.commitment_data.composition, file)

    # Check if WAC CLI tool installed
    if not os.path.exists(config.WAC_CLI_BIN_FILE):
        raise Exception

    # Run WAC CLI to create composite .wasm
    result = subprocess.run([config.WAC_CLI_BIN_FILE, "compose",
                             "-o ", config.COMPOSITE_WASM_FILE,
                             config.WAC_FILE],
                            capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception


def run_wasm():
    # (TODO: maybe store process as state to check on progress later?)

    # Check if wasmtime is installed
    if not os.path.exists(config.WAMSTIME_BIN_FILE):
        raise Exception

    # Run composite WASM binary
    subprocess.Popen(
        # Currently give r/w access to all data files, more granular control requires modifying wasmtime (future work)
        [config.WAMSTIME_BIN_FILE,
         config.COMPOSITE_WASM_FILE,
         "--dir", config.DATA_FOLDER,
         "--dir", config.WASM_OUTPUT_DIR],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True  # Detach subprocess so it keeps running, even if this code crashes
    )

# Check if data or component in VC is exepcted according to CM


def is_verifiable_credential_valid(verifiable_credential: VerifiableCredential, thread_safe_commitment_manifest: ThreadSafeCommitmentManifest):
    # (TODO: add proper identity validation of party (not for demonstrator))

    VC_subject_id = verifiable_credential.credentialSubject.id
    VC_type: str = verifiable_credential.credentialSubject.manifest.type
    VC_manifest_id: str = verifiable_credential.credentialSubject.manifest.id

    CM_data: List[Data] = thread_safe_commitment_manifest.commitment_data.data
    CM_components: List[Component] = thread_safe_commitment_manifest.commitment_data.components

    if VC_type == "data":
        for data in CM_data:
            if data.name == VC_manifest_id and data.participant == VC_subject_id:
                return True

    elif VC_type == "component":
        for component in CM_components:
            if component.name == VC_manifest_id and component.participant == VC_subject_id:
                return True
    else:
        return False


def is_text(file_path: str):
    try:
        with open(file_path, 'r') as file:
            file.read()
        return True
    except:
        return False

import json
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from agent.models.commitment_manifest import ThreadSafeCommitmentManifest
from agent.models.party_submission_state import ThreadSafePartySubmissionState
from agent.routes import lock, attestation, application, status
from agent.routes.lock import HOME_DIR, LOCK_FILE, LOCK_FOLDER

@asynccontextmanager
async def lifespan(app: FastAPI):
    # (TODO: verify that .attestation_agent dir is in fact a tmpfs (to prevent writing to unencrypted disk))
    # (TODO: verify that snpguest and wasmtime are in read-only folders (not for demonstrator))
    
    # Create .attestation_agent dir
    if not os.path.exists(HOME_DIR):
        os.mkdir(HOME_DIR)
    
    # Create empty CommitentManifest
    commitment_manifest = ThreadSafeCommitmentManifest()
    app.state.commitment_manifest = commitment_manifest
    
    # Create empty PartySubmissionState
    party_submission_state = ThreadSafePartySubmissionState()
    app.state.party_submission_state = party_submission_state
    
    # Check if lock already exists on disk, if yes -> load commitment + party-submission state
    file_path = os.path.join(LOCK_FOLDER, LOCK_FILE)
    if os.path.exists(LOCK_FOLDER) and os.path.exists(file_path):    
        with open(file_path, "r") as file:
            config_data = json.load(file)
            await commitment_manifest.lock(**config_data)
            
            # TODO: extract this from CM
            party_data = {"hello": False}
            await party_submission_state.lock(**party_data)
    yield
    
app = FastAPI(lifespan=lifespan)

app.include_router(lock.router)
app.include_router(attestation.router)
app.include_router(application.router)
app.include_router(status.router)
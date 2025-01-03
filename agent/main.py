import json
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

import agent.config as config
from agent.models.commitment_manifest import ThreadSafeCommitmentManifest
from agent.models.party_submission_state import ThreadSafePartySubmissionState
from agent.routes import lock, attestation, application, status

@asynccontextmanager
async def lifespan(app: FastAPI):
    # (TODO: verify that .attestation_agent dir is in fact a tmpfs (to prevent writing to unencrypted disk))
    # (TODO: verify that snpguest and wasmtime are in read-only folders (not for demonstrator))
    
    # Create .attestation_agent dir
    if not os.path.exists(config.AGENT_DIR):
        os.mkdir(config.AGENT_DIR)
    
    # Create empty CommitentManifest
    commitment_manifest = ThreadSafeCommitmentManifest()
    app.state.commitment_manifest = commitment_manifest
    
    # Create empty PartySubmissionState
    party_submission_state = ThreadSafePartySubmissionState()
    app.state.party_submission_state = party_submission_state
    
    # Check if lock already exists on disk, if yes -> load commitment + party-submission state
    if os.path.exists(config.LOCK_FOLDER) and os.path.exists(config.LOCK_FILE):    
        
        with open(config.LOCK_FILE, "r") as file:
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
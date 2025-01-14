import json
import os

from fastapi import FastAPI

from contextlib import asynccontextmanager

import agent.config as config
from agent.models.commitment_manifest import ThreadSafeCommitmentManifest
from agent.models.party_submission_state import ThreadSafePartySubmissionState
from agent.routes import clear, lock, attestation, application, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(config.APPLICATION_API_PATH)
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

        party_data = read_party_submission_state(commitment_manifest)
        await party_submission_state.lock(**party_data)
    yield


def read_party_submission_state(commitment_manifest: ThreadSafeCommitmentManifest):
    submission_state = {}
    for component in commitment_manifest.commitment_data.components:
        dir = os.path.join(config.COMPONENT_FOLDER, "deps")
        if os.path.exists(os.path.join(dir, component.participant, component.name + ".wasm")):
            submission_state[component.name] = True
        else:
            submission_state[component.name] = False

    for data in commitment_manifest.commitment_data.data:
        dir = os.path.join(config.DATA_FOLDER)
        if os.path.exists(os.path.join(dir, data.participant, data.name)):
            submission_state[data.name] = True
        else:
            submission_state[data.name] = False

    return submission_state


app = FastAPI(lifespan=lifespan)

app.include_router(lock.router)
app.include_router(attestation.router)
app.include_router(application.router)
app.include_router(status.router)
if config.DEV_MODE:
    app.include_router(clear.router)
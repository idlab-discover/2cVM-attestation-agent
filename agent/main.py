import json
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from agent.models.commitment_manifest import CommitmentManifest
from agent.routes import lock, attestation, application, status
from agent.routes.lock import HOME_DIR, LOCK_FILE, LOCK_FOLDER

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create .attestation_agent dir
    if not os.path.exists(HOME_DIR):
        os.mkdir(HOME_DIR)
    
    # Check if lock already exists on disk
    file_path = os.path.join(LOCK_FOLDER, LOCK_FILE)
    if os.path.exists(LOCK_FOLDER) and os.path.exists(file_path):    
        with open(file_path, "r") as file:
            config_data = json.load(file)
            app.state.commitment_manifest = CommitmentManifest(**config_data)
    yield
    
app = FastAPI(lifespan=lifespan)

app.include_router(lock.router)
app.include_router(attestation.router)
app.include_router(application.router)
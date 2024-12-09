from fastapi import FastAPI
from app.routes import lock, attestation, application

app = FastAPI()

app.include_router(lock.router)
app.include_router(attestation.router)
app.include_router(application.router)
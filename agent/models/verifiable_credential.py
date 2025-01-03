from typing import Dict, List, Union
from pydantic import BaseModel, Field
from datetime import datetime

class Membership(BaseModel):
    membershipType: str = Field(..., readonly=True)
    website: str = Field(..., readonly=True)
    contact: str = Field(..., readonly=True)
    since: datetime = Field(..., readonly=True)
    
class Manifest(BaseModel):
    id: str = Field(..., readonly=True)
    type: str = Field(..., readonly=True)
    body: Union[str, dict] = Field(..., readonly=True)

class CredentialSubject(BaseModel):
    id: str = Field(..., readonly=True)
    transferRequestId: str = Field(..., readonly=True)
    membership: Membership = Field(..., readonly=True)
    manifest: Manifest = Field(..., readonly=True)
    
class VerifiableCredential(BaseModel):
    context: Union[List[Union[str, Dict[str, str]]], None] = Field(..., alias="@context", readonly=True)
    id: str = Field(..., readonly=True)
    type: List[str] = Field(..., readonly=True)
    issuer: str = Field(..., readonly=True)
    issuanceDate: datetime = Field(..., readonly=True)
    credentialSubject: CredentialSubject = Field(..., readonly=True)
    
    class Config:
        arbitrary_types_allowed = True
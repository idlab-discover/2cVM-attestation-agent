from typing import Dict, List, Union
from pydantic import BaseModel, Field
from datetime import datetime

class Membership(BaseModel):
    membershipType: str
    website: str
    contact: str
    since: datetime
    
class Manifest(BaseModel):
    id: str
    type: str
    body: Union[str, dict]

class CredentialSubject(BaseModel):
    id: str
    transferRequestId: str
    membership: Membership
    manifest: Manifest
    
class VerifiableCredential(BaseModel):
    context: Union[List[Union[str, Dict[str, str]]], None] = Field(..., alias="@context")
    id: str
    type: List[str]
    issuer: str
    issuanceDate: datetime
    credentialSubject: CredentialSubject
    
    class Config:
        arbitrary_types_allowed = True
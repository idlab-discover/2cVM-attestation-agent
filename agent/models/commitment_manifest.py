from pydantic import BaseModel
from typing import List

class Participant(BaseModel):
    name: str
    DID: str

class Component(BaseModel):
    name: str
    participant: str

class Data(BaseModel):
    name: str
    participant: str

class DataPermissionBase(BaseModel):
    type: str
    filename: str

class DataPermissionComposite(DataPermissionBase):
    sources: List[str]
    
class DataPermissionSingle(DataPermissionBase):
    source: str

class Output(BaseModel):
    type: str
    function: str
    participant: str

class Permission(BaseModel):
    component: str
    data_permissions: List[DataPermissionBase]
    output: List[Output]

class CommitmentManifest(BaseModel):
    participants: List[Participant]
    components: List[Component]
    data: List[Data]
    composition: str
    permissions: List[Permission]
    class Config:
        arbitrary_types_allowed = True
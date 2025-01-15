import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional

from agent.models.verifiable_credential import VerifiableCredential


# As CM is only set once, all properties are private and there are no setter.

class Participant(BaseModel):
    name: str = Field(..., readonly=True)
    DID: str = Field(..., readonly=True)


class Component(BaseModel):
    name: str = Field(..., readonly=True)
    participant: str = Field(..., readonly=True)


class Data(BaseModel):
    name: str = Field(..., readonly=True)
    participant: str = Field(..., readonly=True)


class DataPermissionBase(BaseModel):
    type: str = Field(..., readonly=True)


class DataPermissionComposite(DataPermissionBase):
    sources: List[str] = Field(..., readonly=True)


class DataPermissionSingle(DataPermissionBase):
    source: str = Field(..., readonly=True)


class Output(BaseModel):
    type: str = Field(..., readonly=True)
    function: str = Field(..., readonly=True)
    name: str = Field(..., readonly=True)
    participant: str = Field(..., readonly=True)


class Permission(BaseModel):
    component: str = Field(..., readonly=True)
    data_permissions: List[DataPermissionBase] = Field(..., readonly=True)
    output: List[Output] = Field(..., readonly=True)


class CommitmentManifest(BaseModel):
    participants: List[Participant] = Field(..., readonly=True)
    components: List[Component] = Field(..., readonly=True)
    data: List[Data] = Field(..., readonly=True)
    composition: str = Field(..., readonly=True)
    permissions: List[Permission] = Field(..., readonly=True)
    transferRequestIdIMEC: str = Field(..., readonly=True)
    transferRequestIdFabless: str = Field(..., readonly=True)

    class Config:
        arbitrary_types_allowed = True


class ThreadSafeCommitmentManifest():
    _commitment_data: Optional[CommitmentManifest] = None
    _asyncio_lock: asyncio.Lock = None

    def __init__(self):
        self._asyncio_lock = asyncio.Lock()

    # Thread-safe write once to lock TEE to CM
    async def lock(self, **data):
        try:
            await self._asyncio_lock.acquire()
            if self._commitment_data == None:
                self._commitment_data = CommitmentManifest(**data)
        finally:
            self._asyncio_lock.release()

    def is_locked(self):
        return self._commitment_data != None

    # Read-only
    @property
    def commitment_data(self):
        return self._commitment_data

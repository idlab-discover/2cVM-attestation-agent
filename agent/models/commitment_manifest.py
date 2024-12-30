import asyncio
from pydantic import BaseModel
from typing import List, Optional


# As CM is only set once, all properties are private and there are no setter. 

class Participant(BaseModel):
    _name: str
    _DID: str
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def DID(self) -> str:
        return self._DID

class Component(BaseModel):
    _name: str
    _participant: str
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def participant(self) -> str:
        return self._participant

class Data(BaseModel):
    _name: str
    _participant: str
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def participant(self) -> str:
        return self._participant

class DataPermissionBase(BaseModel):
    _type: str
    _filename: str
    
    @property
    def type(self) -> str:
        return self._type

    @property
    def filename(self) -> str:
        return self._filename

class DataPermissionComposite(DataPermissionBase):
    _sources: List[str]
    
    @property
    def sources(self) -> List[str]:
        return self._sources

class DataPermissionSingle(DataPermissionBase):
    _source: str
    
    @property
    def source(self) -> str:
        return self._source

class Output(BaseModel):
    _type: str
    _function: str
    _participant: str
    
    @property
    def type(self) -> str:
        return self._type

    @property
    def function(self) -> str:
        return self._function

    @property
    def participant(self) -> str:
        return self._participant

class Permission(BaseModel):
    _component: str
    _data_permissions: List[DataPermissionBase]
    _output: List[Output]
    
    @property
    def component(self) -> str:
        return self._component

    @property
    def data_permissions(self) -> List[DataPermissionBase]:
        return self._data_permissions

    @property
    def output(self) -> List[Output]:
        return self._output

class CommitmentManifest(BaseModel):
    _participants: List[Participant]
    _components: List[Component]
    _data: List[Data]
    _composition: str
    _permissions: List[Permission]
    
    @property
    def participants(self) -> List[Participant]:
        return self._participants

    @property
    def components(self) -> List[Component]:
        return self._components

    @property
    def data(self) -> List[Data]:
        return self._data

    @property
    def composition(self) -> str:
        return self._composition

    @property
    def permissions(self) -> List[Permission]:
        return self._permissions

    class Config:
        arbitrary_types_allowed = True
        

class ThreadSafeCommitmentManifest():
    _data: Optional[CommitmentManifest] = None
    _asyncio_lock: asyncio.Lock = None

    def __init__(self):
        self._asyncio_lock = asyncio.Lock()
    
    # Thread-safe write once to lock TEE to CM
    async def lock(self, **data):
        try:
            await self._asyncio_lock.acquire()
            if self._data == None:
                self._data = CommitmentManifest(**data)
        finally:
                self._asyncio_lock.release()
                
    def is_locked(self):
        return self._data != None
    
    # Read-only
    @property
    def data(self):
        return self._data
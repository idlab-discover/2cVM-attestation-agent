# This model holds the state of the data and code. E.g., 'is all data and code present?'
# TODO: Maybe change the name? Not sure...

# TODO: test this...

import asyncio
from typing import Dict, Optional
from pydantic import BaseModel, Field, RootModel


class PartySubmissionState(RootModel):
    root: Dict[str, bool] = Field(..., readonly=True)

    def mark_data_as_submitted(self, data_name: str):
        if data_name in self.root:
            self.root[data_name] = True
        else:
            raise KeyError(f"'{data_name}' is not expected.")
        
    def all_data_present(self) -> bool:
        return all(self.root.values())

class ThreadSafePartySubmissionState():
    _data : Optional[PartySubmissionState] = None
    _asyncio_lock: asyncio.Lock = None

    def __init__(self):
        self._asyncio_lock = asyncio.Lock()
        
    async def lock(self, **data):
        try:
            await self._asyncio_lock.acquire()
            if self._data == None:
                self._data = PartySubmissionState(**data)
                print(self._data)
        finally:
                self._asyncio_lock.release()
        
    async def mark_data_as_submitted(self, data_name: str):
        try:
            await self._asyncio_lock.acquire()
            if self._data != None:
                self._data.mark_data_as_submitted(data_name)
        finally:
                self._asyncio_lock.release()
    
    async def all_data_present(self):
        try:
            await self._asyncio_lock.acquire()
            if self._data != None:
                return self._data.all_data_present()
        finally:
                self._asyncio_lock.release()
                
    @property
    def data(self):
        return self._data
        
        
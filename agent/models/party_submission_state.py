# This model holds the state of the data and code. E.g., 'is all data and code present?'
# TODO: Maybe change the name? Not sure...

# TODO: test this...

import asyncio
from typing import Dict, Optional
from pydantic import BaseModel, RootModel


class PartySubmissionState(RootModel):
    Dict[str, bool]

    def mark_data_as_submitted(self, data_name: str):
        if data_name in self.status:
            self.status[data_name] = True
        else:
            raise KeyError(f"'{data_name}' is not expected.")
        
    def is_all_data_present(self) -> bool:
        return all(self.status.values())

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
        finally:
                self._asyncio_lock.release()
        
    async def mark_data_as_submitted(self, data_name: str):
        try:
            await self._asyncio_lock.acquire()
            if self._data != None:
                self._data.mark_data_as_submitted(data_name)
        finally:
                self._asyncio_lock.release()
    
    async def is_all_data_present(self):
        try:
            await self._asyncio_lock.acquire()
            if self._data != None:
                return self._data.is_all_data_present()
        finally:
                self._asyncio_lock.release()
        
        
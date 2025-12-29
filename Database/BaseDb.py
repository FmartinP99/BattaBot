from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from Database.Classes.Remind import CreateRemind, RemindRow

class BaseDb(ABC):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]  

    @abstractmethod
    async def connect(self, tableName: str | None = None, sql_file: str | None = None):
        pass

    @classmethod
    def get_instance(cls) -> BaseDb:
        """Return the singleton instance if it exists, else None."""
        return cls._instances.get(cls, None)
    
    @abstractmethod
    async def add_reminder(self, remind: CreateRemind) -> int:
        pass

    # Read
    @abstractmethod
    async def get_reminder(self, reminder_id: int) -> RemindRow | None:
       pass
    
    @abstractmethod
    async def get_reminders(self, server_id: str | None, user_id: str | None, channel_id: str | None) -> List[RemindRow]:
       pass

    # Update
    @abstractmethod
    async def update_reminder(self, reminder_id: int, **kwargs) -> bool:
        pass

    # Delete
    @abstractmethod
    async def delete_reminder(self, reminder_id: int) -> bool:
        pass

    # Delete multiple
    @abstractmethod
    async def delete_reminders(self, reminder_ids: list[int]) -> int:
        pass
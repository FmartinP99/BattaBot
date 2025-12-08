from abc import ABC, abstractmethod
from typing import List, Optional

from Database.Classes.Remind import CreateRemind, RemindRow

class BaseDb(ABC):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]

    @abstractmethod
    def connect(self):
        pass

    @classmethod
    def get_instance(cls):
        """Return the singleton instance if it exists, else None."""
        return cls._instances.get(cls, None)
    
    async def add_reminder(self, remind: CreateRemind) -> int:
        pass

    # Read
    async def get_reminder(self, reminder_id: int) -> Optional[RemindRow]:
       pass
    
    async def get_all_reminders(self) -> List[RemindRow]:
        pass

    async def get_reminders(self, server_id: Optional[str], user_id: Optional[str]) -> List[RemindRow]:
       pass

    # Update
    async def update_reminder(self, reminder_id: int, **kwargs) -> bool:
        pass

    # Delete
    async def delete_reminder(self, reminder_id: int) -> bool:
        pass
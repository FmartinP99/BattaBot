from typing import List, Optional
from Database.Classes.Remind import CreateRemind, RemindRow
from Services.BaseService import BaseService
from utils.remindme_helper import make_naive

class RemindmeService(BaseService):

    def __init__(self,):
         super().__init__()

    async def add_remindme(self, server_id,  channel_id, user_id, remind_time, remind_text) -> int:
        row: CreateRemind = CreateRemind(
        server_id=server_id,
        channel_id=channel_id,
        user_id=user_id,
        remind_time=make_naive(remind_time),
        remind_text=remind_text,
        remind_happened=0  
    )
        inserted_id = await self.databaseHandler.add_reminder(row)
        return inserted_id

    async def get_reminder(self, row_id: int) -> Optional[RemindRow]:
        return await self.databaseHandler.get_reminder(row_id) 
    
    async def get_all_reminders(self) -> List[RemindRow]:
        reminder_rows = await self.databaseHandler.get_reminders()
        return reminder_rows

    async def get_reminders_by_server_and_user(self, server_id: str, user_id: str) -> List[RemindRow]:
        reminder_rows = await self.databaseHandler.get_reminders(server_id=server_id, user_id=user_id)
        return reminder_rows
    
    async def delete_reminder(self, reminder_id: int) -> bool:
        isDeleted = await self.databaseHandler.delete_reminder(reminder_id)
        return isDeleted
    
    async def delete_reminders(self, row_indexes: List[int]) -> int:
        return await self.databaseHandler.delete_reminders(row_indexes)
    
    async def update_reminder_reminded_column(self, rowId: int, value: bool) -> bool:
        return await self.databaseHandler.update_reminder(rowId, REMIND_HAPPENED=value)


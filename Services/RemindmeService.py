from typing import List
from Database.BaseDb import BaseDb
from Database.Classes.Remind import CreateRemind, RemindRow
from Database.SQLite3Db import SQLite3Db


class RemindmeService:

    def __init__(self,):
        self.databaseHandler: BaseDb = SQLite3Db.get_instance() # to-do: branch this if it will support multiple database classes.

    async def add_remindme(self, server_id,  channel_id, user_id, remind_time, remind_text) -> int:
        row: CreateRemind = CreateRemind(
        server_id=server_id,
        channel_id=channel_id,
        user_id=user_id,
        remind_time=remind_time,
        remind_text=remind_text,
        remind_happened=0  
    )
        inserted_id = await self.databaseHandler.add_reminder(row)
        return inserted_id
    
    async def get_all_reminders(self) -> List[RemindRow]:
        reminder_rows = await self.databaseHandler.get_all_reminders()
        return reminder_rows
    
    async def delete_reminders(self, row_indexes: List[int]) -> int:
        return await self.databaseHandler.delete_reminders(row_indexes)
    
    async def update_reminder_reminded_column(self, rowId: int, value: bool) -> bool:
        return await self.databaseHandler.update_reminder(rowId, REMIND_HAPPENED=value)


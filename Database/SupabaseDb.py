from typing import List, Optional
from supabase import AsyncClient, acreate_client
from Database.BaseDb import BaseDb
from Database.Classes.Remind import CreateRemind, RemindRow

class SupabaseDb(BaseDb):

    def __init__(self, url: str, key: str):
        self._url = url
        self._key = key
        self._client: Optional[AsyncClient] = None

    async def connect(self) -> Optional[AsyncClient]:
        if self._client is None:
            self._client = await acreate_client(self._url, self._key)
            print("Connected to Supabase.")
        return self._client
    
    async def add_reminder(self, remind: CreateRemind) -> int:
        client = await self.connect()

        data = {
            "SERVER_ID": remind.server_id,
            "CHANNEL_ID": remind.channel_id,
            "USER_ID": remind.user_id,
            "REMIND_TIME": remind.remind_time.isoformat(),
            "REMIND_TEXT": remind.remind_text,
            "REMIND_HAPPENED": remind.remind_happened,
        }

        print(data)

        response = await client.table("Reminders").insert(data).execute()

        print(response)

        # Supabase returns inserted rows
        if response.data:
            return response.data[0]["id"]  # Adjust key name to your schema
        
        return None
    
    async def get_reminder(self, reminder_id: int) -> Optional[RemindRow]:
       pass
    
    async def get_reminders(self, server_id: Optional[str], user_id: Optional[str]) -> List[RemindRow]:
       pass

    async def update_reminder(self, reminder_id: int, **kwargs) -> bool:
        pass

    async def delete_reminder(self, reminder_id: int) -> bool:
        pass

    async def delete_reminders(self, reminder_ids: list[int]) -> int:
        pass
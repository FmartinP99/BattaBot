from typing import List
from supabase import AsyncClient, acreate_client
from Database.BaseDb import BaseDb
from Database.Classes.Remind import CreateRemind, RemindRow
from dateutil.parser import isoparse

class SupabaseDb(BaseDb):

    def __init__(self, url: str, key: str):
        self._url = url
        self._key = key
        self._client: AsyncClient | None = None

    async def connect(self) -> AsyncClient | None:
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

        response = await client.table("Reminders").insert(data).execute()

        # Supabase returns inserted rows
        if response.data:
            return response.data[0]["id"]  # Adjust key name to your schema
        
        return None
    
    async def get_reminder(self, reminder_id: int) -> RemindRow | None:
        client = await self.connect()

        try:
            response = await client.table("Reminders").select("*").eq("id", reminder_id).single().execute()
        except Exception as e:
            print(e)
            return None
        
        if not response.data:
            print(f"Supabase error: {response.error}")
            return None
        
        row = response.data 
        if row is None:
            return None

        return self._convert_reminder_to_remindrow(row)
    

    
    async def get_reminders(self, server_id: str | None = None, user_id: str | None = None, channel_id: str | None=None) -> List[RemindRow]:
        client = await self.connect()
        query = client.table("Reminders").select("*")
        
        if server_id is not None:
            query = query.eq("SERVER_ID", server_id)
        
        if user_id is not None:
            query = query.eq("USER_ID", user_id)
        
        if channel_id is not None:
            query = query.eq("CHANNEL_ID", user_id)
        
        try:
            response = await query.execute()
        except Exception as e:
            print(e)
            return []
            
        if not response.data:
            print(f"Supabase query returned no data or failed: {response.data}")
            return []

        rows = response.data or [] 
        reminders: List[RemindRow] = []

        for row in rows:
            if (reminder := self._convert_reminder_to_remindrow(row)) is not None:
                reminders.append(reminder)

        return reminders
      

    async def update_reminder(self, reminder_id: int, **kwargs) -> bool:
        if not kwargs:
            return False

        client = await self.connect()

        try:
            response = await client.table("Reminders").update(kwargs).eq("id", reminder_id).execute()
        except Exception as e:
            print(e)
            return False
        
        if not response.data:
            print(f"Supabase error: {response.error}")
            return False
        
        return bool(response.data and len(response.data) > 0)

    async def delete_reminder(self, reminder_id: int) -> bool:
        client = await self.connect()
        try:
            response = await client.table("Reminders").delete().eq("id", reminder_id).execute()
        except Exception as e:
            print(e)
            return False
        
        if not response.data:
            print(f"Supabase error: {response.error}")
            return False
        
        return bool(response.data and len(response.data) > 0)

    async def delete_reminders(self, reminder_ids: list[int]) -> int:
        if not reminder_ids:
            return 0  
        
        client = await self.connect()

        try:
            response = await client.table("Reminders").delete().in_("id", reminder_ids).execute()
        except Exception as e:
            print(e)
            return 0
    
        if not response.data:
            print(f"Supabase error: {response.error}")
            return 0
        
        return len(response.data or [])
    
    def _convert_reminder_to_remindrow(self, row: dict) -> RemindRow | None:
        if row is None:
            return None
        
        try:
            created_at = isoparse(row["CREATED_AT"]) if row.get("CREATED_AT") else None
            remind_time = isoparse(row["REMIND_TIME"]) if row.get("REMIND_TIME") else None
        except ValueError as e:
            print(f"Error parsing datetime: {e}")
            return None

        try:
            return RemindRow(
                id=int(row.get("id", 0)),
                server_id=str(row.get("SERVER_ID", "")),
                channel_id=str(row.get("CHANNEL_ID", "")),
                user_id=str(row.get("USER_ID", "")),
                created_at=created_at,
                remind_time=remind_time,
                remind_text=str(row.get("REMIND_TEXT", "")),
                remind_happened=bool(row.get("REMIND_HAPPENED", False))
            )
        except Exception as e:
            print(f"Failed to convert row to RemindRow: {e}, row={row}")
            return None
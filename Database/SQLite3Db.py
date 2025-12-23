import asyncio
from datetime import datetime
import os
from sqlite3 import Connection
from threading import Lock
from typing import List, Optional
from Database.BaseDb import BaseDb
import sqlite3

from Database.Classes.Remind import CreateRemind, RemindRow


class SQLite3Db(BaseDb):

    def __init__(self, db_path):
        self._db_path = db_path
        self._connection: Optional[Connection] = None
        self._lock = Lock()

    async def connect(self, tableName: Optional[str] = None, sql_file: Optional[str] = None) -> Optional[Connection]:
        def sync_connect():
            if self._connection is None:
                try:
                    self._connection = sqlite3.connect(self._db_path, check_same_thread=False)
                    self._connection.row_factory = sqlite3.Row
                    print(f"Connected to SQLite database at {self._db_path}")
                    if self._connection and tableName and sql_file and not self.table_exists(tableName):
                        isCreated = self.run_sql_file(sql_file)
                        if not isCreated:
                            print(f"{tableName} has not been created!")
                    elif self._connection and tableName and sql_file:
                        print("Connection happened but table was not created.")
                except sqlite3.Error as e:
                    print(f"Error connecting to SQLite: {e}")
            return self._connection
        return await asyncio.to_thread(sync_connect)
    
    def isConnected(self) -> bool:
        return self._connection is not None

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            print("SQLite connection closed.")

    def table_exists(self, table_name: str) -> bool:
        if not os.path.exists(self._db_path):
            return False
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?;
            """, (table_name,))
            exists = cursor.fetchone() is not None
            return exists
        except Exception as e:
            return False

    def run_sql_file(self, sql_file: str) -> bool:
        if not os.path.exists(sql_file):
            return False
        try:
            cursor = self._connection.cursor()
            with open(sql_file, "r") as f:
                cursor.executescript(f.read())
            self._connection.commit()
            return True
        except Exception as e:
            return False
        
    def _parse_datetime(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        
    def _convert_reminder_to_remindrow(self, row:sqlite3.Row)-> Optional[RemindRow]:
        if row is None:
            return None

        created_at = self._parse_datetime(row["CREATED_AT"])
        remind_time = self._parse_datetime(row["REMIND_TIME"]) if row["REMIND_TIME"] else None

        return RemindRow(
            id=row["ID"],
            server_id=row["SERVER_ID"],
            channel_id=row["CHANNEL_ID"],
            user_id=row["USER_ID"],
            created_at=created_at,
            remind_time=remind_time,
            remind_text=row["REMIND_TEXT"],
            remind_happened=True if row["REMIND_HAPPENED"] else False
        )
        
    async def add_reminder(self, remind: CreateRemind) -> int:
        with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Reminders (SERVER_ID, CHANNEL_ID, USER_ID, REMIND_TIME, REMIND_TEXT, REMIND_HAPPENED)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (remind.server_id, remind.channel_id, remind.user_id,
                remind.remind_time, remind.remind_text, remind.remind_happened))
            conn.commit()
            return cursor.lastrowid

    async def get_reminder(self, reminder_id: int) -> Optional[RemindRow]:
        conn = await self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Reminders WHERE ID=?", (reminder_id,))
        row = cursor.fetchone()
        return self._convert_reminder_to_remindrow(row)
 
    async def get_reminders(self, server_id: Optional[str]=None, user_id: Optional[str]=None, channel_id: Optional[str]=None) -> List[RemindRow]:
        conn = await self.connect()
        cursor = conn.cursor()

        conditions = []
        params = []

        if server_id is not None:
            conditions.append("SERVER_ID = ?")
            params.append(server_id)

        if user_id is not None:
            conditions.append("USER_ID = ?")
            params.append(user_id)

        if channel_id is not None:
            conditions.append("CHANNEL_ID = ?")
            params.append(channel_id)

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        query = "SELECT * FROM Reminders" + where_clause

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall() or []

        return [
            reminder
            for row in rows
            if (reminder := self._convert_reminder_to_remindrow(row)) is not None
        ]

   
    async def update_reminder(self, reminder_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        
        with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            fields = ", ".join(f"{key}=?" for key in kwargs.keys())
            values = list(kwargs.values())
            values.append(reminder_id)
            sql = f"UPDATE Reminders SET {fields} WHERE ID=?"
            cursor.execute(sql, values)
            conn.commit()
            return cursor.rowcount > 0
      

    async def delete_reminder(self, reminder_id: int) -> bool:
        with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Reminders WHERE ID=?", (reminder_id,))
            conn.commit()
            return cursor.rowcount > 0
       
    
    async def delete_reminders(self, reminder_ids: list[int]) -> int:
        if not reminder_ids:
            return False  # nothing to delete
     
        with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()

            placeholders = ",".join(["?"] * len(reminder_ids))

            sql = f"DELETE FROM Reminders WHERE ID IN ({placeholders})"
            cursor.execute(sql, reminder_ids)
            conn.commit()

            return cursor.rowcount
    
    async def execute(self, sql: str, params: tuple = ()):
        with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            self._connection.commit()

       
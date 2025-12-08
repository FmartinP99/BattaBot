from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateRemind:
    server_id: str
    channel_id: str
    user_id: str
    remind_time: str
    remind_text: str
    remind_happened: int

@dataclass(frozen=True)
class RemindRow:
    """Represents a row fetched from the Reminders table."""
    id: int
    server_id: str
    channel_id: str
    user_id: str
    created_at: datetime 
    remind_time: datetime
    remind_text: str
    remind_happened: bool  # 0 or 1

    def __str__(self) -> str:
        status = "✅ Done" if self.remind_happened else "⏳ Pending"
        return (
            f"Reminder ID: {self.id}\n"
            f"Server: {self.server_id} | Channel: {self.channel_id} | User: {self.user_id}\n"
            f"Created At: {self.created_at}\n"
            f"Remind Time: {self.remind_time}\n"
            f"Text: {self.remind_text}\n"
            f"Status: {status}"
        )

from datetime import datetime, timedelta
from typing import List
from Database.Classes.Remind import RemindRow
from Services.RemindmeService import RemindmeService
from Websocket.websocket_message_classes import WebsocketGetRemindersResponse, WebsocketReminderStatus
from utils.remindme_helper import get_gmt_offset


class WebsocketService:

    def __init__(self):
        self.reminderService: RemindmeService = RemindmeService()

    async def get_reminders_for_user_for_server(self, server_id: int, user_id: int) -> WebsocketGetRemindersResponse:
        try:
            response: WebsocketGetRemindersResponse = {
                "success": True,
                "serverId": str(server_id),
                "memberId": str(user_id),
                "reminders": []
            }
            remind_rows: List[RemindRow] = await self.reminderService.get_reminders_by_server_and_user(server_id=server_id, user_id=user_id)
        
            nowtime = datetime.now()
            gmt_offset = get_gmt_offset()
            nowtime = datetime.now() + timedelta(hours=gmt_offset)

            for reminder in remind_rows:
                status = WebsocketReminderStatus.HAPPENED if reminder.remind_happened else WebsocketReminderStatus.DUE if not reminder.remind_happened and reminder.remind_time < nowtime else WebsocketReminderStatus.PENDING
                response["reminders"].append({
                    "id": reminder.id,
                    "channel_id": reminder.channel_id,
                    "created_at": reminder.created_at,
                    "remind_time": reminder.remind_time,
                    "remind_text": reminder.remind_text,
                    "status": status.value
                })
            return response
        except Exception as e:
            print(e)
            response : WebsocketGetRemindersResponse = {
                "success": False,
                "errorText": "Querying the reminders has failed." 
            }
            return response

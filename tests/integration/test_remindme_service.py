import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import pytest
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_add_and_get_reminder(remindme_service):
    remind_time = datetime.now(tz=timezone.utc) + timedelta(hours=1)

    reminder_id = await remindme_service.add_remindme(
        server_id="server1",
        channel_id="channel1",
        user_id="user1",
        remind_time=remind_time,
        remind_text="Test reminder"
    )

    assert isinstance(reminder_id, int)

    reminder = await remindme_service.get_reminder(reminder_id)

    assert reminder is not None
    assert reminder.server_id == "server1"
    assert reminder.channel_id == "channel1"
    assert reminder.user_id == "user1"
    assert reminder.remind_text == "Test reminder"
    assert reminder.remind_happened == 0

@pytest.mark.asyncio
async def test_get_all_reminders(remindme_service):
    for i in range(3):
        await remindme_service.add_remindme(
            server_id="server1",
            channel_id="channel1",
            user_id=f"user{i}",
            remind_time=datetime.utcnow(),
            remind_text=f"Reminder {i}"
        )

    reminders = await remindme_service.get_all_reminders()
    assert len(reminders) == 3

async def test_get_reminders_by_server_and_user(remindme_service):
    await remindme_service.add_remindme(
        server_id="server1",
        channel_id="channel1",
        user_id="user1",
        remind_time=datetime.utcnow(),
        remind_text="User1 Reminder"
    )

    await remindme_service.add_remindme(
        server_id="server1",
        channel_id="channel1",
        user_id="user2",
        remind_time=datetime.utcnow(),
        remind_text="User2 Reminder"
    )

    reminders = await remindme_service.get_reminders_by_server_and_user(
        server_id="server1",
        user_id="user1"
    )

    assert len(reminders) == 1
    assert reminders[0].user_id == "user1"

@pytest.mark.asyncio
async def test_update_remind_happened(remindme_service):
    reminder_id = await remindme_service.add_remindme(
        server_id="server1",
        channel_id="channel1",
        user_id="user1",
        remind_time=datetime.utcnow(),
        remind_text="Update test"
    )

    updated = await remindme_service.update_reminder_reminded_column(
        rowId=reminder_id,
        value=True
    )

    assert updated is True

    reminder = await remindme_service.get_reminder(reminder_id)
    assert reminder.remind_happened == 1

@pytest.mark.asyncio
async def test_delete_reminder(remindme_service):
    reminder_id = await remindme_service.add_remindme(
        server_id="server1",
        channel_id="channel1",
        user_id="user1",
        remind_time=datetime.utcnow(),
        remind_text="Delete test"
    )

    deleted = await remindme_service.delete_reminder(reminder_id)
    assert deleted is True

    reminder = await remindme_service.get_reminder(reminder_id)
    assert reminder is None

@pytest.mark.asyncio
async def test_delete_multiple_reminders(remindme_service):
    ids = []
    for i in range(3):
        rid = await remindme_service.add_remindme(
            server_id="server1",
            channel_id="channel1",
            user_id="user1",
            remind_time=datetime.utcnow(),
            remind_text=f"Bulk {i}"
        )
        ids.append(rid)

    deleted_count = await remindme_service.delete_reminders(ids)
    assert deleted_count == 3

    reminders = await remindme_service.get_all_reminders()
    assert reminders == []


@pytest.mark.asyncio
async def test_update_remind_happened_column(remindme_service):
    reminder_id = await remindme_service.add_remindme(
        server_id="server1",
        channel_id="channel1",
        user_id="user1",
        remind_time=datetime.utcnow(),
        remind_text="Update column test"
    )

    reminder = await remindme_service.get_reminder(reminder_id)
    assert reminder.remind_happened == 0

    updated_true = await remindme_service.update_reminder_reminded_column(
        rowId=reminder_id,
        value=True
    )

    assert updated_true is True
    reminder = await remindme_service.get_reminder(reminder_id)
    assert reminder.remind_happened == 1

    updated_false = await remindme_service.update_reminder_reminded_column(
        rowId=reminder_id,
        value=False
    )

    assert updated_false is True
    reminder = await remindme_service.get_reminder(reminder_id)
    assert reminder.remind_happened == 0

    updated_nonexistent = await remindme_service.update_reminder_reminded_column(
        rowId=9999,  
        value=True
    )
    assert updated_nonexistent is False
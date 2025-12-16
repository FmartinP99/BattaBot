import warnings
from pydantic import PydanticDeprecatedSince20

# turn off deprecation warnings, because pytest didnt migrate to newer version yet.
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)

import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import pytest
from Database.SQLite3Db import SQLite3Db
from Services.RemindmeService import RemindmeService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DB_PATH = os.path.join(BASE_DIR, "../.." ,"Database", "files", "databaseTest.db")
CREATE_TABLE_SQL = os.path.join(BASE_DIR, "../.." ,"Database", "files", "CreateReminderTable.sql")

@pytest.fixture(scope="session")
async def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_handler():
    db = SQLite3Db(TEST_DB_PATH)
    await db.connect("Reminders", CREATE_TABLE_SQL)
    yield db
    db.close()

@pytest.fixture(scope="function", autouse=True)
async def clean_db(db_handler):
    await db_handler.execute("DELETE FROM Reminders")
    yield

@pytest.fixture
async def remindme_service(db_handler):
    service = RemindmeService()
    await db_handler.execute("DELETE FROM Reminders")
    yield service
    await db_handler.execute("DELETE FROM Reminders")
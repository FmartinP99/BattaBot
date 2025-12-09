from Database.SupabaseDb import SupabaseDb
from Database.BaseDb import BaseDb
from Database.SQLite3Db import SQLite3Db
from globals import GLOBAL_CONFIGS, DatabaseType


class BaseService:
    def __init__(self):
        self.databaseHandler = self._init_db_handler()

    @staticmethod
    def _init_db_handler() -> BaseDb:
        if GLOBAL_CONFIGS.database_type == DatabaseType.SQLITE:
            return SQLite3Db.get_instance()
        elif GLOBAL_CONFIGS.database_type == DatabaseType.SUPABASE:
            return SupabaseDb.get_instance()
        else:
            raise ValueError("Unsupported database type")
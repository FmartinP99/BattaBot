from dataclasses import dataclass
from enum import Enum
import json

class DatabaseType(Enum):
    SQLITE = "SQLITE"
    SUPABASE = "SUPABASE"

@dataclass
class Config:
    prefix: str
    owner_id: int
    bot_id: int
    cover: str
    local_media_path: str
    ffmpeg: str
    websocket_enabled: bool
    database_type: DatabaseType
    supabase_url: str
    supabase_key: str

def load_config(path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["database_type"] = DatabaseType[data["database_type"]]

    return Config(**data)

GLOBAL_CONFIGS = load_config(path="files/config.json")
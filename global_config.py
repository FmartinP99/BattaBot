from dataclasses import dataclass
from enum import Enum
import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "files", "config.json")

class DatabaseType(Enum):
    SQLITE = "SQLITE"
    SUPABASE = "SUPABASE"

@dataclass(frozen=True)
class WebsocketConfig:
    ip: str
    port: str
    log_level: str

@dataclass(frozen=True)
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
    websocket_config: WebsocketConfig

def load_config(path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["database_type"] = DatabaseType[data["database_type"]]
    
    ws_cfg = WebsocketConfig(**data["websocket_config"])
    data["websocket_config"] = ws_cfg

    return Config(**data)

GLOBAL_CONFIGS = load_config(path=CONFIG_PATH)
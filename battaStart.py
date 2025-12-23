from Database.SupabaseDb import SupabaseDb
from Database.BaseDb import BaseDb
from Database.SQLite3Db import SQLite3Db
from botMain import bot, token, load_extensions
from global_config import GLOBAL_CONFIGS, DatabaseType
import asyncio
from Websocket.websocketManager import ws_manager
from Websocket.websocketMessageDistributor import WebsocketMessageDistributor

if GLOBAL_CONFIGS.websocket_enabled:
    from fastapi import FastAPI, WebSocket
    import uvicorn
    app = FastAPI()
    connected_clients = set()

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws_manager.connect(ws)
        try:
            while True:
                data = await ws.receive_text()
                await ws_message_distributor.handle_incoming_ws_message(data)
        finally:
            ws_manager.disconnect(ws)


async def run_websocket_server():
    if  GLOBAL_CONFIGS.websocket_enabled:
        config = uvicorn.Config(app, host=GLOBAL_CONFIGS.websocket_config.ip, port=GLOBAL_CONFIGS.websocket_config.port, log_level=GLOBAL_CONFIGS.websocket_config.log_level)
        server = uvicorn.Server(config)
        await server.serve()


async def create_database_handler() -> None:
    
    if GLOBAL_CONFIGS.database_type == DatabaseType.SQLITE:
        db = SQLite3Db("Database/files/database.db")
        await db.connect("Reminders", "Database/files/CreateReminderTable.sql")

    elif GLOBAL_CONFIGS.database_type == DatabaseType.SUPABASE:
        db = SupabaseDb(GLOBAL_CONFIGS.supabase_url, GLOBAL_CONFIGS.supabase_key)
        await db.connect()
    else:
        raise ValueError("Unsupported database type")
    
    global ws_message_distributor
    ws_message_distributor = WebsocketMessageDistributor(bot)

async def main_run():
    await create_database_handler()
    await load_extensions()
    await bot.start(token)

async def main():
    await asyncio.gather(
        run_websocket_server(),
        main_run()
    )

if __name__ == "__main__":
    asyncio.run(main())
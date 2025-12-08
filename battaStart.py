from Database.BaseDb import BaseDb
from Database.SQLite3Db import SQLite3Db
from botMain import bot, token, load_extensions
from globals import g_api, g_database, g_websocket_enabled
from import_routes import battAPP_blueprints
import asyncio
from websocketManager import ws_manager

#USING QUART CAUSES THE BOT TO SHUT DOWN IF YOU EDIT ITS SOURCE CODE WHILE IT IS RUNNING
#DONT TURN ON UNLESS YOU WANT TO HAVE YOUR OWN (FOR NOW)

if g_websocket_enabled:
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
                cog = bot.get_cog("Websocket");
                if cog:
                    await cog.handleIncomingWsMessage(data)
                else:
                    raise ValueError("Websocket cog is not found!")
        finally:
            ws_manager.disconnect(ws)


async def run_websocket_server():
    if  g_websocket_enabled:
        config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()



async def notify_frontend(message: str):
    for ws in list(connected_clients):
        try:
            print("message sent")
            await ws.send_text(message)
        except Exception:
            print("error while sending message")
            connected_clients.remove(ws)



async def main_run():

        
    # if g_api is True and g_database:
    #     from quart import Quart
    #     battAPP = Quart(__name__)

    #     for blueprint in battAPP_blueprints:
    #         battAPP.register_blueprint(blueprint)

    #     async with bot:
    #         bot.loop.create_task(battAPP.run_task(host="0.0.0.0", port=49420))
    #         await load_extensions()
    #         await bot.start(token)
    # else:
        dbHandler: BaseDb = SQLite3Db("Database/files/database.db")
        dbHandler.connect("Reminders", "Database/files/CreateReminderTable.sql")
        await load_extensions()
        await bot.start(token)

async def main():
    await asyncio.gather(
        run_websocket_server(),
        main_run()
    )

if __name__ == "__main__":
    asyncio.run(main())
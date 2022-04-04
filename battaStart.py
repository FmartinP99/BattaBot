from botMain import bot, token
from globals import g_api, g_database
from import_routes import battAPP_blueprints

#USING QUART CAUSES THE BOT TO SHUT DOWN IF YOU EDIT ITS SOURCE CODE WHILE IT IS RUNNING
#DONT TURN ON UNLESS YOU WANT TO HAVE YOUR OWN (FOR NOW)

if g_api is True and g_database:
    from quart import Quart
    battAPP = Quart(__name__)

    for blueprint in battAPP_blueprints:
        battAPP.register_blueprint(blueprint)

    bot.loop.create_task(battAPP.run_task('0.0.0.0', 49420))

bot.run(token)

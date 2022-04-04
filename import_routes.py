from globals import g_api, g_database

# USING QUART CAUSES THE BOT TO SHUT DOWN IF YOU EDIT ITS SOURCE CODE WHILE IT IS RUNNING

battAPP_blueprints = []

if g_api is True and g_database:
    try:
        from QuartRoutes.quart_routes import conn_with_other_battabot
        battAPP_blueprints.append(conn_with_other_battabot)
    except ModuleNotFoundError:
        pass  # it's a personal module I'm just too lazy to do 2 separate builds

    try:
        from QuartRoutes.for_the_api import api
        battAPP_blueprints.append(api)
    except ModuleNotFoundError:
        pass  # it's a personal module I'm just too lazy to do 2 separate builds

    try:
        from QuartRoutes.for_the_gui import gui
        battAPP_blueprints.append(gui)
    except ModuleNotFoundError:
        pass  # it's a personal module I'm just too lazy to do 2 separate builds

import sys
import traceback
from datetime import datetime
import re

g_cover = ""
g_ownerid = None
g_botid = None
g_localMediaPlayerFolderPath = ""
g_prefix = ""
g_database = False
g_api = False
g_ffmpeg = ""
g_websocket_enabled = False

def set_globals():
    global g_cover
    global g_ownerid
    global g_botid
    global g_localMediaPlayerFolderPath
    global g_prefix
    global g_database
    global g_api
    global g_ffmpeg
    global g_websocket_enabled

    for line in open('Files/globalsDefaultValueImport.txt', 'r', encoding='utf-8'):
        var = re.search('\"(.*)\"', line).group(1)

        if line.startswith("COVER"):
            g_cover = var

        elif line.startswith("OWNER_ID"):
            try:
                g_ownerid = int(var)
            except ValueError:
                raise ValueError("PLEASE PROVIDE YOUR ID AND YOUR BOT ID IN THE globalsDefaultValueImport.txt file")


        elif line.startswith("BOT_ID"):
            try:
                g_botid = int(var)
            except ValueError:
                raise ValueError("PLEASE PROVIDE YOUR ID AND YOUR BOT ID IN THE globalsDefaultValueImport.txt file")

        elif line.startswith('LOCAL_MEDIAPLAYER_FOLDER_PATH'):
            g_localMediaPlayerFolderPath = var.replace("\\", "/")

        elif line.startswith('PREFIX'):
            g_prefix = var

        elif line.startswith('DATABASE'):
            if var.lower() == "true":
                g_database = True

        elif line.startswith('API'):
            if var.lower() == "true":
                g_api = True

        elif line.startswith("FFMPEG"): 
            g_ffmpeg = var.replace("\\", "/")
        
        elif line.startswith('WEBSOCKET_ENABLED'):
            if var.lower() == "true":
                g_websocket_enabled = True

    if g_cover == "":
        g_cover = "Files/profpiccropped.png"


set_globals()

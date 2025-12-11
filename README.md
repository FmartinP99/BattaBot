# バッタ Bot

## About:

Discordbot written in Python. Also features optional websocket communication. For example with: [Battabot-WebUI](https://github.com/FmartinP99/Battabot-WebUI)

Recommended Python version: `3.9`.

## Install:

- Clone the repository.
- Create a virtual enviroment with the correct python version.
- Activate the environment.
- run `pip install -r requirements.txt`.
- Create a `.token0` file inside the root folder, that contains your bot's api key.
- Set the variables inside the `files/config.json`
- If you want to use the player function you must have FFMPEG installed somewhere in your system, provide it's bin/ffmpeg.exe 's path in the `config.json`.
- Run the battaStart.py file.

## Features:

- Reminder function. These reminders are stored in the database.
- Audio playing from the computer. (Currently MP3 only).
- Optional real-time websocket communication. (More will be added in the future).
- TraceMoe search.
- MyAnimeList search feature

## Additional:

- As of now, this program can work with `SQLITE` (default) and `SUPABASE` databases. You can easily add your own database to it if you prefer something else. All you have to do is create a class that inherits from `BaseDB` and implement it's abstract functions, modify the `_init_db_handler()` of the `BaseService` class, and add a new enum inside the `DatabaseType` (you have to use the same values inside the `config.json`'s `database_type` field).

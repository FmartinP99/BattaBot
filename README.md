# バッタBot
Discordbot written in Python with (optional) MongoDB.

Install:
- Clone the repo.
- Add your .token0 file in the root folder.
- Run the command inside the root folder: pip install -r requirements.txt.
- Set the variables in the Files/globalsDefaultValueImport.txt and Files/globalsForTheDatabase.txt (if you want MongoDB).
- If you want to use the player function you must have FFMPEG installed somewhere in your system, provide it's bin/ffmpeg.exe 's path.
- Run the battaStart.py file.
- If Jinja2 error happens try:
- pip install Jinja2==2.11.3 Markupsafe==1.1.1

Features:
- MyAnimeList search.
- TraceMoe search.
- Reminder function.

- Mediaplayer (local and youtube, FFMPEG required)
 
- Leveling and Xp system (MongoDB required)
- Message count and groupping by date (MongoDB required)
- Groups feature (MongoDB required)

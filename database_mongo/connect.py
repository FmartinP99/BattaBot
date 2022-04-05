import re
from pymongo import MongoClient
import os
import sys
from datetime import date, datetime

connected = False


def start():

    global connected


    for line in open('Files/globalsForTheDatabase.txt', 'r', encoding='utf-8'):
        var = re.search('\"(.*)\"', line).group(1)

        if line.startswith("CONNECTION"):
            connection = var


        elif line.startswith("DB_NAME"):
            db_name = var

        elif line.startswith("DB_MESSAGES_NAME"):
            db_messages = var

        elif line.startswith("DB_USERS_NAME"):
            db_users = var

        elif line.startswith("DB_GROUPS_NAME"):
            db_groups = var

    cluster = MongoClient(f"{connection}", connect=False)
    db = cluster[f"{db_name}"]
    collection_messages = db[f"{db_messages}"]
    collection_users = db[f"{db_users}"]
    collection_groups = db[f"{db_groups}"]
    connected = True
    return collection_messages, collection_users, collection_groups



if not connected:
    collection_messages, collection_users, collection_groups = start()


def insert(server_id: int, name: str, discriminator: int, user_id: int) -> str:
    """Inserts the person into the database"""

    user = collection_users.find_one(({"serverID": server_id, "userID": user_id}))
    if not user:
        collection_users.insert_one({"_id": f"User+{user_id}+{server_id}", "serverID": server_id, "userID": user_id,  "Name": name,
                                    "Level": 1, "Exp": 0, "Discriminator": discriminator})
        return f"{name} has been added to the database!!"
    else:
        return f"{name} is already in the database!!"


def message_query(server_id: int, user_id: int) -> None:
    """Counts the messages for the members in the database per day"""

    today = datetime.today().strftime('%Y-%m-%d')
    today_date = datetime.today().replace(hour=0, minute=0, microsecond=0)

    id = "MessageObject:" + "+" + str(today) + "+" + str(server_id)
    user = collection_users.find_one({"serverID": server_id, "userID": user_id})
    message = collection_messages.find_one({"_id": id})
    if message:
        detailed_message = collection_messages.find_one({"_id": id, "Users.Name": user['Name'], "Users.Discriminator": user['Discriminator']})
        if detailed_message:
            collection_messages.update_one({"_id": id, "Users.Name": user['Name'], "Users.Discriminator": user['Discriminator']}, {"$inc": {"Users.$.Messages": 1}})
        else:
            collection_messages.update_one({"_id": id}, {"$push": {"Users": {"Name": user['Name'], "Discriminator": user['Discriminator'], "Messages": 1}}})
    else:
        collection_messages.insert_one({"_id": id, "Date": today_date, "Users": [{"Name": user['Name'], "Discriminator": user['Discriminator'], "Messages": 1}]})


def update(server_id: int, user_id: int, exp: int) -> None:
    """Updates the XP and LEVEL for the members in the database"""

    collection_users.update_one({"serverID": server_id, "userID": user_id}, {"$inc": {"Exp": exp}})
    user = collection_users.find_one({"serverID": server_id, "userID": user_id}, {"_id":0, "Exp": 1, "Level": 1})
    if user:
        xp = int(user['Exp'])
        level = int(user['Level'])
        try:
            if xp > level * 1000:
                collection_users.update_one({"serverID": server_id, "userID": user_id},
                                      {"$inc": {"Exp": -(level * 1000), "Level": +1}})
        except:
            pass


def find(server_id: int, user_id: int) -> bool:
    """Finds an user based on their serverID and userID"""

    user = collection_users.find_one({"serverID": server_id, "userID": user_id})
    if user:
        return True
    else:
        return False


def get_user(server_id: int, name: str, discriminator: int = None) -> dict:
    """Checks if the user is in the database and returns it."""

    if discriminator is None:
        user = collection_users.find_one({"serverID": server_id, "Name":re.compile(name, re.IGNORECASE)})
    else:
        user = collection_users.find_one({"serverID": server_id, "Name": re.compile(name, re.IGNORECASE), "Discriminator": int(discriminator)})
    return user


def get_me(server_id: int, user_id: int) -> tuple:
    """Returns None, None, None, if can't find the user, otherwise returns name, xp, level"""

    try:
        user = collection_users.find_one({"serverID": server_id, "userID": user_id}, {"_id": 0, "Exp": 1, "Level": 1, "Name": 1})
        name = user['Name']
        xp = int(user['Exp'])
        level = int(user['Level'])
        return name, xp, level

    except:
        return None, None, None,


def update_me(server_id: int, user_id: int, newName: str, newDiscriminator: int) -> tuple or None:
    """Updates the user's name and discriminator in the database"""

    user = collection_users.find_one({"serverID": server_id, "userID": user_id}, {"_id": 0, "Name": 1, "Discriminator": 1})
    name = user['Name']
    discriminator = user['Discriminator']

    if name == newName and discriminator == newDiscriminator:
        name = None
        discriminator = None

    else:
        collection_users.update_one({"serverID": server_id, "userID": user_id}, {"$set": {"Name": newName, 'Discriminator': newDiscriminator}}, upsert=False)

    return name, discriminator


def find_or_create_group(name: str, server_id: int, user_id: int) -> bool:

    groupObject = "GroupObject:" + "+" + name + "+" + str(server_id)
    group = collection_groups.find_one({"_id": groupObject})

    if group:
        return True
    else:
        collection_groups.insert_one({"_id": groupObject, "Name": name, "serverID":server_id, "Users": [{"userID": user_id}]})
        return False


def join_group(groupname: str, server_id: int, user_id: int, userName: str) -> str:

    groupObject = "GroupObject:" + "+" + groupname + "+" + str(server_id)
    group = collection_groups.find_one({"_id": groupObject})


    if group:
        detailed_group = collection_groups.find_one({"_id": groupObject, "Users.serverID": server_id, "Users.userID": user_id})
        if not detailed_group:
            collection_groups.update_one({"_id": groupObject}, {"$push": {"Users": {"userID": user_id}}})
            return f"{userName} has joined group {groupname}!"
        else:
            return f"{userName} has already joined group {groupname}!"
    else:
        return f"there is no group called {groupname}!"


def ping_group(name: str, server_id: int, user_id: int) -> dict:

    groupObject = "GroupObject:" + "+" + name + "+" + str(server_id)
    group = collection_groups.find_one({"_id": groupObject, "serverID": server_id, "Users.userID": user_id})

    userDict = {}
    if group:
        userDict = group['Users']

    return userDict


def list_group(server_id: int) -> list[str]:

    regex = re.compile("^GroupObject:", re.IGNORECASE)
    groups = collection_groups.find({"_id": regex, "serverID": server_id},{"_id": 0, "Name": 1})
    groupNames = []

    for group in groups:
        groupNames.append(group['Name'])
    return groupNames


def replace():
    pass



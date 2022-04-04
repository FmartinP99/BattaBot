from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
from database_mongo.connect import collection_messages, collection_users
from datetime import datetime, timedelta
import calendar
from database_mongo.plot.monthDate import get_month
from matplotlib.pyplot import figure

def get_data(server_id, queryMonthorDayLength=None):

    users = collection_users.find({"_id": {"$regex": "^User" }, "serverID": server_id}, {"_id":0, "Name":1, "Discriminator":1,})

    if queryMonthorDayLength is None:
        limit = 14
        messages = collection_messages.find({"_id": {"$regex": f"^MessageObject.*?{server_id}"}},
                                   {"_id": 0,"Date": 1, "Users": 1}).sort('Date', -1).limit(limit)
        make_list(users, messages, month_length=0, addition=f"Last {limit} days")

    else:

        try:
            queryMonthorDayLength = min(int(queryMonthorDayLength), 366)
            messages = collection_messages.find({"_id": {"$regex": f"^MessageObject.*?{server_id}"}},
                                       {"_id": 0, "Date": 1, "Users": 1}).sort('Date', -1).limit(queryMonthorDayLength)

            make_list(users, messages, month_length=0, addition=f"Last {queryMonthorDayLength} days")

        except:
            try:
                addition, accepted_month = get_month(queryMonthorDayLength)
                now = datetime.now()
                month = calendar.monthrange(now.year, accepted_month)
                datetimeBegin = datetime(year=now.year, month=accepted_month, day=1, hour=0, minute=0, microsecond=0)
                datetimeEnd = datetime(year=now.year, month=accepted_month, day=month[1], hour=0, minute=0, microsecond=0)
                messages = collection_messages.find({"_id": {"$regex": f"^MessageObject.*?{server_id}"}, "Date": {"$lte": datetimeEnd,
                                               "$gte": datetimeBegin}}, {"_id": 0, "Date": 1, "Users": 1}).sort('Date', -1)
                for msg in messages:
                    make_list(users, messages, month_length=min(month[1], messages.count()-1), addition=addition)
                    break

                else:
                    return "Empty"

            except:
                return "Error"


def make_list(users, messages, month_length, addition):


    def_dict = defaultdict(list) # doesnt have to be defaultDict
    userList = list()
    messageList = list()
    dateList = list()
    dictionary = {}
    for user in users:
        userList.append(f"{user['Name']}#{user['Discriminator']}")

    for message in messages:
        messageList.insert(0, message)

        dateList.insert(0, str(message['Date'])[5:10])

    for message in messageList:
        for user in userList:
            dictionary[user] = 0
            def_dict[message['Date']] = dictionary

        for user in message['Users']:
            temp = f"{user['Name']}#{user['Discriminator']}"
            dictionary[temp] = int(user['Messages'])
            def_dict[message['Date']] = dictionary
        dictionary = {}

    msglist = list()

    for i in range(0, len(userList)):  # it creates a nested list per user
        msglist.append([])

    for key, value in def_dict.items():
        for key2, value2 in value.items():                  # it works because the "value" is a dictionary
            index = 0
            for user in userList:
                if user == key2:
                    msglist[index].append(value2)
                index += 1

    plot(userList, msglist, dateList, addition)

def plot(userList, msglist, dateList, addition):


    figure(num=None, figsize=(16+len(dateList), 9+len(userList)), dpi=60, facecolor='lightgrey', edgecolor='k')
    plt.rcParams['figure.facecolor'] = "lightgrey"
    plt.rcParams['axes.facecolor'] = "lightgrey"
    plt.rcParams['lines.color'] = "white"
    plt.rc('legend', fontsize=26)
    plt.rc('axes', titlesize=30, labelsize=30)
    plt.rc('ytick', labelsize=22)
    plt.rc('xtick', labelsize=18)

    index = 0
    while index < len(userList):
        plt.plot(dateList, msglist[index], marker='o', label=f"{userList[index]}", linewidth=3)
        index += 1

    plt.title(f"Messages Sent Daily\n( {addition} )")
    plt.xlabel("Date")
    plt.ylabel("Number of Messages\n")
    plt.grid(True)
    plt.legend()
    plt.savefig("Files/diagram.png")
    plt.close()













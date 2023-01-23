from collections import defaultdict
import matplotlib.pyplot as plt
from database_mongo.connect import collection_messages, collection_users
from datetime import datetime, timedelta
import calendar
from database_mongo.plot.monthDate import get_month
from matplotlib.pyplot import figure


def get_data(server_id, query_month_or_day_length=None):

    users = collection_users.find({"_id": {"$regex": "^User" }, "serverID": server_id}, {"_id":0, "Name":1, "Discriminator":1,})

    if query_month_or_day_length is None:
        limit = 14
        messages = collection_messages.find({"_id": {"$regex": f"^MessageObject.*?{server_id}"}},
                                   {"_id": 0,"Date": 1, "Users": 1}).sort('Date', -1).limit(limit)
        make_list(users, messages, month_length=0, addition=f"Last {limit} days")

    else:

        try:
            now = datetime.now()
            query_month_or_day_length = min(int(query_month_or_day_length), 365)
            query_time_beginning = datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, microsecond=0) - timedelta(days=query_month_or_day_length)
            messages = collection_messages.find({"_id": {"$regex": f"^MessageObject.*?{server_id}"}, "Date": {"$gte": query_time_beginning}},
                                       {"_id": 0, "Date": 1, "Users": 1}).sort('Date', -1)

            make_list(users, messages, month_length=0, addition=f"Last {query_month_or_day_length} days")

        except:
            try:
                addition, accepted_month = get_month(query_month_or_day_length)
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
                    if value2 > 0:
                        msglist[index].append(value2)
                    else:
                        msglist[index].append(None)
                index += 1

    plot(userList, msglist, dateList, addition)


def plot(user_list, msg_list, date_list, addition):

    figure(num=None, figsize=(16 + len(date_list), 9 + len(user_list)), dpi=60, facecolor='lightgrey', edgecolor='k')
    plt.rcParams['figure.facecolor'] = "lightgrey"
    plt.rcParams['axes.facecolor'] = "lightgrey"
    plt.rcParams['lines.color'] = "white"
    plt.rc('legend', fontsize=26)
    plt.rc('axes', titlesize=30, labelsize=30)
    plt.rc('ytick', labelsize=22)
    plt.rc('xtick', labelsize=18)

    index = 0
    while index < len(user_list):
        plt.plot(date_list, msg_list[index], marker='o', label=f"{user_list[index]}", linewidth=3)
        print(msg_list[index])
        index += 1

    plt.title(f"Messages Sent Daily\n( {addition} )")
    plt.xlabel("Date")
    plt.ylabel("Number of Messages\n")
    plt.grid(True)
    plt.legend()
    plt.savefig("Files/diagram.png")
    plt.close()













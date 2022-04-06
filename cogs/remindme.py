from discord.ext import commands
from datetime import datetime, timedelta
from dataclasses import dataclass
from botMain import IS_BOT_READY
import asyncio
import re
import os
import sys


class RemindMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    separator = "|!!|"

    @commands.command()
    async def remindme(self, context, time, *args):
        nowtime = datetime.now()
        _Year = nowtime.year
        _Month = nowtime.month
        _Day = nowtime.day
        _Hour = nowtime.hour
        _Minute = nowtime.minute
        _Microsecond = nowtime.microsecond

        valid_regex = False
        message_to_send = ""

        _split_char_index = time.find(':')

        # check if 03:00 or 3:00 and make it 03:00

        if len(time) == 4 and ":" in time:
            time = "0" + time

        if self.regexes(time) == False:
            await context.send("The format of the time is wrong!")
            return
        else:
            if self.regexes(time) == 4:
                message_to_send = ' '.join(args)

                __Hour = int(time[:2])
                __Minute = int(time[3:5])

                if __Hour > _Hour or (__Hour == _Hour and __Minute > _Minute):
                    set_time = datetime(_Year, _Month, _Day, __Hour, __Minute, 0, _Microsecond)
                    valid_regex = True

                elif __Hour < _Hour or (__Hour == _Hour and __Minute <= _Minute):
                    set_time = datetime(_Year, _Month, _Day, __Hour, __Minute, 0, _Microsecond) + timedelta(days=1)
                    valid_regex = True

                else:
                    await context.send("I can't ping you in the past.")

            elif self.regexes(time) == 5 and (str(args[0]).startswith("+")):
                set_time = datetime(_Year, _Month, _Day, _Hour, _Minute, 0, _Microsecond) + timedelta(minutes=int(time))
                message_to_send = ' '.join(args)
                message_to_send = message_to_send[1:]  # cuts the "+"
                valid_regex = True


            elif self.regexes(time) == 3:
                valid_regex = False  # not sure if the regex  yyyy-mm-dd hh:mm  format, and it's not in the past
                time = time + " " + args[0]

                _split_char_index = time.find(':')

                if time[_split_char_index - 2] == " ":
                    time = time[:_split_char_index - 1] + "0" + time[_split_char_index - 1:]

                try:
                    regex_retrun = self.regexes(time)
                    if regex_retrun == 1 or regex_retrun == 2:
                        message_to_send = ""
                        if len(args) > 0:
                            message_to_send = ' '.join(args[1:])

                        if regex_retrun == 1:
                            __Year = int(time[0:4])
                            __Month = int(time[5:7])
                            __Day = int(time[8:10])
                            __Hour = int(time[11:13])
                            __Minute = int(time[14:16])
                            set_time = datetime(__Year, __Month, __Day, __Hour, __Minute, 0, _Microsecond)
                        else:
                            __Year = nowtime.year
                            __Month = int(time[0:2])
                            __Day = int(time[3:5])
                            __Hour = int(time[6:8])
                            __Minute = int(time[9:11])
                            set_time = datetime(__Year, __Month, __Day, __Hour, __Minute, 0, _Microsecond)
                            if set_time < nowtime:
                                set_time = datetime(__Year + 1, __Month, __Day, __Hour, __Minute, 0, _Microsecond)

                        if set_time > nowtime:
                            valid_regex = True
                        else:
                            await context.send("I can't ping you in the past.")
                    else:
                        await context.send("The format of the time is wrong!")
                except Exception:
                    print(sys.exc_info())
                    await context.send("The format of the time is wrong!")

            else:
                await context.send("The format of the time is wrong!")
                sys.exc_info()

            if valid_regex is True:
                sleepTimer = (set_time - nowtime).total_seconds()
                await context.send(f"Timer set to: {set_time.strftime('%Y-%m-%d  %H:%M')}")
                await self.remindme_writefile(context, set_time, message_to_send)
                await asyncio.sleep(sleepTimer)
                await self.ping_bot(context, message_to_send, context.message.author.id)

    async def ping_bot(self, context, msg, author):

        if msg != "":
            await context.send(f"<@{author}>\n{str(msg)}")
        else:
            await context.send(context.author.mention)

    def regexes(self, time):

        if re.match('(([12]\\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01]))\\s((0[0-9]|1[0-9]|2[0-4]):[0-5][0-9]))', time):
            return 1
        elif re.match('(((0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01]))\\s((0[0-9]|1[0-9]|2[0-4]):[0-5][0-9]))', time):
            return 2
        elif re.match('(([12]\\d{3}-)?(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01]))', time):
            return 3
        elif re.match('^[0-2]?[0-9]:[0-5][0-9]', time):
            return 4
        elif re.match('^[1-9][0-9]{0,3}$', time):
            return 5
        else:
            return False

    async def remindme_writefile(self, context, time, *args):
        message = " ".join(args)

        with open('Files/reminders.txt', 'a', encoding='utf-8', newline='\n') as f:
            f.write(
                f"{context.message.channel.id}{self.separator}{context.message.author.id}{self.separator}{time}{self.separator}{message}{self.separator}\n")

    async def remindme_checkfile(self):

        if os.stat('Files/reminders.txt').st_size != 0:
            with open('Files/reminders.txt', 'r', encoding='utf-8', newline='\n') as f:
                if f:
                    record_array = []
                    for line in f:
                        try:
                            currentline = line.split(f"{self.separator}")
                            sentTime = currentline[2]

                            _year = int(sentTime[0:4])
                            _month = int(sentTime[5:7])
                            _day = int(sentTime[8:10])
                            _hour = int(sentTime[11:13])
                            _minute = int(sentTime[14:16])
                            _microsecond = int(sentTime[20:26])

                            getTime = datetime(_year, _month, _day, _hour, _minute, 0, _microsecond)

                            if (getTime - datetime.now()).total_seconds() > 0:
                                record_array.append(Record(int(currentline[0]), int(currentline[1]), getTime, currentline[3]))
                            else:
                                print(f"This is the past! {getTime}")
                        except Exception:
                            print("An error occurred during the reading of the file. Maybe empty?")
                            sys.exc_info()

                    record_array.sort()

            with open('Files/reminders.txt', 'w', encoding='utf-8', newline='\n') as f:

                for record in record_array:
                    f.write(record.to_line(self.separator) + "\n")

            await self.remindme_readfile()


    async def remindme_readfile(self):

        lines_array = []
        with open('Files/reminders.txt', 'r', encoding='utf-8', newline='\n') as f:
            if f:
                for line in f:
                    lines_array.append(line)

        for line in lines_array:
            currentline = line.split(f"{self.separator}")
            channelid = int(currentline[0])
            authorid = int(currentline[1])
            author = f'<@{authorid}>'
            sentTime = currentline[2]
            sentMessage = self.separator.join(currentline[3:len(currentline) - 1])

            _year = int(sentTime[0:4])
            _month = int(sentTime[5:7])
            _day = int(sentTime[8:10])
            _hour = int(sentTime[11:13])
            _minute = int(sentTime[14:16])

            getTime = datetime(_year, _month, _day, _hour, _minute)
            sleepTimer = (getTime - datetime.now()).total_seconds()

            await self.auto_mention(sleepTimer, channelid, sentMessage, author)

    async def auto_mention(self, sleepTimer, channelid, sentMessage, author):

        channel = self.bot.get_channel(channelid)

        await asyncio.sleep(sleepTimer)
        await channel.send(f"{author}\n{str(sentMessage)}")
        await self.delete_first_line()

    async def delete_first_line(self):

        with open('Files/reminders.txt', 'r', encoding='utf-8', newline='\n') as file:
            lines = file.read().splitlines(True)
        with open('Files/reminders.txt', 'w', encoding='utf-8', newline='\n') as file:
            file.writelines(lines[1:])


    @commands.Cog.listener()
    async def on_ready(self):
        await self.remindme_checkfile()

    @remindme.error
    async def remindme_error(self, context, error):
        print(error)


def setup(bot):
    bot.add_cog(RemindMe(bot))


@dataclass()
class Record:

    channelID: int
    userID: int
    date: datetime
    message: str


    def __gt__(self, other):
        if isinstance(other, Record):
            return self.date > other.date

    def __lt__(self, other):
        if isinstance(other, Record):
            return self.date < other.date

    def __eq__(self, other):
        if isinstance(other, Record):
            return self.date == other.date

    def __ne__(self, other):
        if isinstance(other, Record):
            return self.date != other.date

    def __ge__(self, other):
        if isinstance(other, Record):
            return self.date >= other.date

    def __le__(self, other):
        if isinstance(other, Record):
            return self.date <= other.date

    def to_line(self, separator: str) -> str:
        return f"{self.channelID}{separator}{self.userID}{separator}{self.date}{separator}{self.message}{separator}"
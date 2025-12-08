from enum import Enum, auto
from discord.ext import commands
from datetime import datetime, timedelta
from dataclasses import dataclass
from Database.BaseDb import BaseDb
from Database.Classes.Remind import CreateRemind
from Services.RemindmeService import RemindmeService
from botMain import check_owner
import asyncio
import re
import os
import sys
from discord.ext import tasks
from Database.SQLite3Db import SQLite3Db

class TimeFormat(Enum):
    FULL_DATE = auto()       # yyyy-mm-dd HH:MM
    DATE_NO_YEAR = auto()    # mm-dd HH:MM
    DATE_ONLY = auto()       # yyyy-mm-dd or mm-dd
    TIME_ONLY = auto()       # HH:MM
    NUMBER = auto()          # integer
    INVALID = auto()

class RemindMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminderService: RemindmeService = RemindmeService()
        
    separator = "|!!|"

    @commands.command(aliases=['rm'])
    async def remindme(self, context, time, *args):
        nowtime = datetime.now()
        _Year = nowtime.year
        _Month = nowtime.month
        _Day = nowtime.day
        _Hour = nowtime.hour
        _Minute = nowtime.minute
        _Second = nowtime.second
        _Microsecond = nowtime.microsecond

        valid_regex = False
        message_to_send = ""

        _split_char_index = time.find(':')

        # check if 03:00 or 3:00 and make it 03:00

        if len(time) == 4 and ":" in time:
            time = "0" + time

        time_format = self.regexes(time)

        if time_format == TimeFormat.INVALID:
            await context.send("The format of the time is wrong!")
            return
        else:
            if time_format == TimeFormat.TIME_ONLY:
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

            elif time_format == TimeFormat.NUMBER and (str(args[0]).startswith("+")):
                set_time = datetime(_Year, _Month, _Day, _Hour, _Minute, _Second, _Microsecond) + timedelta(minutes=int(time))
                message_to_send = ' '.join(args)
                message_to_send = message_to_send[1:]  # cuts the "+"
                valid_regex = True


            elif time_format == TimeFormat.DATE_ONLY:
                if len(args) == 0:
                    await context.send("You must provide a time after the date. Example: `12-09 14:30`")
                    return
                valid_regex = False  # not sure if the regex  yyyy-mm-dd hh:mm  format, and it's not in the past
                time = time + " " + args[0]

                _split_char_index = time.find(':')

                if time[_split_char_index - 2] == " ":
                    time = time[:_split_char_index - 1] + "0" + time[_split_char_index - 1:]

                try:
                    time_format = self.regexes(time)
                    if time_format == TimeFormat.FULL_DATE or time_format == TimeFormat.DATE_NO_YEAR:
                        message_to_send = ""
                        if len(args) > 0:
                            message_to_send = ' '.join(args[1:])

                        if time_format == TimeFormat.FULL_DATE:
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
                sleep_timer = (set_time - nowtime).total_seconds()
                await context.send(f"Timer set to: {set_time.strftime('%Y-%m-%d  %H:%M')}")
                rowId = await self.add_remindme_to_database(context.message.guild.id, context.message.channel.id, context.message.author.id, set_time, message_to_send)
                await self.auto_mention(sleep_timer, context.message.guild.id, context.message.channel.id, context.message.author.id, rowId, message_to_send)

    async def auto_mention(self, sleep_timer: float, server_id: int, channel_id: int, author: int, row_id: int, message: str):
        await asyncio.sleep(sleep_timer)
        await self.ping_bot(server_id, channel_id, message, author, row_id)

    async def ping_bot(self, server_id:int, channel_id:int, msg: str, author: int, row_id: int):

        guild = self.bot.get_guild(server_id)
        if not guild:
            print(f"Guild {server_id} not found")
            return

        channel = guild.get_channel(channel_id) # to-do: megnézni hogy text type-e a channel
        if not channel:
            print(f"Channel {channel_id} not found")
            return

        content = f"<@{author}>"
        if msg:
            content += f"\n{msg}"
        await channel.send(content)
        await self.reminderService.update_reminder_reminded_column(row_id, True)

    def regexes(self, time: str) -> TimeFormat:

        if re.match(r'([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))\s((0[0-9]|1[0-9]|2[0-4]):[0-5][0-9])', time):
            return TimeFormat.FULL_DATE

        elif re.match(r'((0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))\s((0[0-9]|1[0-9]|2[0-4]):[0-5][0-9])', time):
            return TimeFormat.DATE_NO_YEAR

        elif re.match(r'(([12]\d{3}-)?(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))', time):
            return TimeFormat.DATE_ONLY

        elif re.match(r'^[0-2]?[0-9]:[0-5][0-9]$', time):
            return TimeFormat.TIME_ONLY

        elif re.match(r'^[1-9][0-9]{0,3}$', time):
            return TimeFormat.NUMBER

        return TimeFormat.INVALID

    async def check_remindmes_in_db(self):

        reminder_rows = await self.reminderService.get_all_reminders()
        if reminder_rows is None:
            return

        reminders_to_mention = [r for r in reminder_rows if not r.remind_happened]
        nowTime = datetime.now()
        rows_to_delete = [r for r in reminder_rows if r.remind_happened]
        for reminder in reminders_to_mention:
            # was in the past therefore no mention, maybe delete these later?
            sleepTimer = (reminder.remind_time - nowTime).total_seconds()
            if sleepTimer < 0:
                continue
            asyncio.create_task(self.auto_mention(sleepTimer, 
                                                  int(reminder.server_id), 
                                                  int(reminder.channel_id), 
                                                  int(reminder.user_id),
                                                  int(reminder.id),
                                                  reminder.remind_text, 
                                                  ))
        

        
        if len(rows_to_delete) > 0: 
            deleted_row_numbers = await self.reminderService.delete_reminders([r.id for r in rows_to_delete ])
            print(f"After scanning the remidners table {deleted_row_numbers} were deleted!")
            for row in rows_to_delete:
                print("-----------")
                print(row)
                print("-----------")
        

    async def add_remindme_to_database(self, server_id,  channel_id, user_id, remind_time, remind_text):
        inserted_id = await self.reminderService.add_remindme(server_id,  channel_id, user_id, remind_time, remind_text)
        return inserted_id
    
    @commands.check(check_owner)
    @commands.command(aliases=['grm'])
    async def get_all_remindmes(self, context):
        reminders = await self.reminderService.get_all_reminders()
        if reminders is None:
            return
        
        for reminder in reminders:
            print(reminder)
            print()


    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_remindmes_in_db()

    @remindme.error
    async def remindme_error(self, context, error):
        print(error)


async def setup(bot):
    await bot.add_cog(RemindMe(bot))



from discord.ext import commands
from datetime import datetime
from Database.Classes.Remind import RemindRow
from Services.RemindmeService import RemindmeService
from botMain import check_owner
import asyncio
from utils.remindme_helper import get_remindme_datetime_and_message

class RemindMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminderService: RemindmeService = RemindmeService()
        self.scheduled_tasks: dict[int, asyncio.Task] = {}
        
    @commands.command(aliases=['rm'])
    async def remindme(self, context: commands.Context, *args):
        
        nowtime = datetime.now()
        set_time, message_to_send = get_remindme_datetime_and_message(*args)

        if set_time is None:
            await context.send(message_to_send)
            return

        sleep_timer = (set_time - nowtime).total_seconds()
        await context.send(f"Timer set to: {set_time.strftime('%Y-%m-%d  %H:%M')}")
        rowId = await self.add_remindme_to_database(context.message.guild.id, context.message.channel.id, context.message.author.id, set_time, message_to_send)
        task = asyncio.create_task(self.auto_mention(
            sleep_timer, 
            context.message.guild.id, 
            context.message.channel.id, 
            context.message.author.id, 
            rowId, 
            message_to_send))
        self.scheduled_tasks[rowId] = task

    @commands.command(aliases=['getmyrms'])
    async def get_remindmes_for_user(self, context: commands.Context):
        remind_rows = await self.reminderService.get_reminders_by_server_and_user(server_id=context.guild.id, user_id=context.author.id)
        reminder_messages = self.format_reminders_to_discord_batches(remind_rows[:100])

        if len(remind_rows) > 0:
            msg = f"You have {len(remind_rows)} reminders!"
            if len(remind_rows) > 100:
                msg += " The maximum queryable number is 100!"
            await context.channel.send(msg)

        for msg in reminder_messages:
            await context.channel.send(msg)
            await asyncio.sleep(2)

    @commands.command(aliases=['deleterm', 'removerm'])
    async def delete_remindme_for_user(self, context: commands.Context, row_id=None):
        if not row_id:
            await context.send("You have to provide an id to delete.")
            return
        
        try:
            row_id = int(row_id)
        except ValueError:
            await context.send("The ID must be a valid integer.")
            return
        
        remind_row = await self.reminderService.get_reminder(row_id)

        if not remind_row or int(remind_row.server_id) != context.guild.id:
            await context.send(f"There is no reminder with the id {row_id}.")
            return
        
        if int(remind_row.user_id) != context.author.id:
            await context.send("This remindme does not belong to you!")
            return
        
        isDeleted = await self.reminderService.delete_reminder(remind_row.id)

        if isDeleted:
            message = f"The #${remind_row.id} remindme has been deleted!"
            task_cancelled = self.cancel_task(remind_row.id)
            if not task_cancelled:
                message += "\n The task has not been cancelled since it did not exist."
            await context.send(f"The #{remind_row.id} remindme has been deleted!")
        else:
            await context.send(f"The #{remind_row.id} remindme has not been deleted!")
    
    @commands.command(aliases=['clearmyrms'])
    async def clear_remindmes(self, context: commands.Context):
        remind_rows = await self.reminderService.get_reminders_by_server_and_user(server_id=context.guild.id, user_id=context.author.id)
        nowtime  = datetime.now()
        old_remind_row_ids = [r.id for r in remind_rows if not r.remind_happened and (r.remind_time - nowtime).total_seconds() < 0]

        deleted_rows_num = await self.reminderService.delete_reminders(old_remind_row_ids)
        await context.send(f"{deleted_rows_num} remindme has been deleted!")

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

    async def check_remindmes_in_db(self):

        reminder_rows = await self.reminderService.get_all_reminders()
        if reminder_rows is None:
            return

        reminders_to_mention = [r for r in reminder_rows if not r.remind_happened]
        nowTime = datetime.now()
        rows_to_delete = [r for r in reminder_rows if r.remind_happened]
        for reminder in reminders_to_mention:
            # was in the past therefore no mention, can delete them with .clearmyrms
            sleepTimer = (reminder.remind_time - nowTime).total_seconds()
            if sleepTimer < 0:
                continue
            task = asyncio.create_task(self.auto_mention(sleepTimer, 
                                                  int(reminder.server_id), 
                                                  int(reminder.channel_id), 
                                                  int(reminder.user_id),
                                                  int(reminder.id),
                                                  reminder.remind_text, 
                                                  ))
            
            self.scheduled_tasks[reminder.id] = task
        
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

    def cancel_task(self, taskId):
        task = self.scheduled_tasks.pop(taskId, None)
        if task:
            task.cancel()  
            return True
        return False   

    def format_reminders_to_discord_batches(self, rows: list[RemindRow], batch_size: int = 10) -> list[str]:
   
        if not rows:
            return ["No reminders found."]
        
        messages = []
        current_lines = []
        nowtime = datetime.now()
        for i, row in enumerate(rows, 1):
            remind_unix = int(row.remind_time.timestamp())
            status = "✅ Happened" if row.remind_happened else "❌ Due past" if not row.remind_happened and row.remind_time < nowtime else "⏳ Pending"
            safe_text = row.remind_text.replace("`", "\\`")

            reminder_text = f"**{i}. Reminder #{row.id}** - {status}\n" \
                f"<t:{remind_unix}:F> (<t:{remind_unix}:R>)\n" \
                f"<@{row.user_id}> in <#{row.channel_id}>"

            if safe_text:
                reminder_text += f"\n> {safe_text}"

            current_lines.append(reminder_text)

            # if batch_size reached or next reminder would overflow discord limit
            if len(current_lines) >= batch_size or sum(len(l) for l in current_lines) > 1900:
                messages.append("\n".join(current_lines))
                current_lines = []

        # add any leftover reminders
        if current_lines:
            messages.append("\n".join(current_lines))

        return messages
    
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



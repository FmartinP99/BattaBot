from discord.ext import commands
from database_mongo import connect



class Group(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.connect = connect

    @commands.command(aliases=['gc'])
    async def group_create(self, context, *name):

        groupName = ""

        if not name or str(name).isspace() is True:
            await context.send("You have to provide a name to create a group!")
            return

        for word in name:
            groupName = groupName + " " + word

        groupName = groupName.strip()

        if connect.find_or_create_group(groupName, context.message.guild.id, context.message.author.id) is True:
            await context.send(f"{groupName} group already exists!")
        else:
            await context.send(f"{groupName} group has been created!")

    @commands.command(aliases=['gj'])
    async def group_join(self, context, *name):

        groupName = ""

        for word in name:
            groupName = groupName + " " + word
        groupName = groupName.strip()
        await context.send(connect.join_group(groupName, context.message.guild.id, context.message.author.id, context.message.author))


    @commands.command(aliases=['gp'])
    async def group_ping(self, context, *name):

        groupName = ""

        for word in name:
            groupName = groupName + " " + word
        groupName = groupName.strip()
        users = connect.ping_group(groupName, context.message.guild.id, context.message.author.id)

        message = ""

        if len(users) > 0:
            for user in users:
                if user['userID'] != context.message.author.id:
                    message = message + f"<@{user['userID']}>" + " "

            message = message.strip()
        else:
            message = f"There are either no group called {groupName}, or you are not in the group!"

        await context.send(message)

    @commands.command(aliases=['gl'])
    async def group_list(self, context):

        groups = connect.list_group(context.message.guild.id)
        groupList = ""
        print(groups)
        if groups:
            for group in groups:

                if groupList != "":
                    groupList = groupList + ", " + group
                else:
                    groupList = group

        groupList = groupList.strip()
        await context.send(f"The groups are: {groupList}")




def setup(bot):
    bot.add_cog(Group(bot))

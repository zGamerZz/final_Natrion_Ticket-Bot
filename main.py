#Version: 1.9
#GitHub: https://github.com/Simoneeeeeeee/Discord-Select-Menu-Ticket-Bot
#Discord: discord.gg/ycZDpat7dB

import discord
import json
from discord import *
from discord.ext import commands, tasks
from cogs.ticket_system import Ticket_System
from cogs.ticket_commands import Ticket_Command

#This will get everything from the config.json file
with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

BOT_TOKEN = config["token"]  #Your Bot Token from https://discord.dev
GUILD_ID = config["guild_id"] #Your Server ID aka Guild ID  
CATEGORY_ID1 = config["category_id_1"] #Category 1 where the Bot should open the Ticket for the Ticket option 1
CATEGORY_ID2 = config["category_id_2"] #Category 2 where the Bot should open the Ticket for the Ticket option 2

bot = commands.Bot(intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Bot Started | {bot.user.name}')
    richpresence.start()
###
#Bot Status, Counting all opened Tickets in the Server. You need to add/change things if you have more or less than 2 Categories
@tasks.loop(minutes=1)
async def richpresence():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print(f'Guild with ID {GUILD_ID} not found.')
        return
    
    category1 = discord.utils.get(guild.categories, id=int(CATEGORY_ID1))
    category2 = discord.utils.get(guild.categories, id=int(CATEGORY_ID2))
    
    if category1 is None:
        print(f'Category with ID {CATEGORY_ID1} not found.')
    if category2 is None:
        print(f'Category with ID {CATEGORY_ID2} not found.')
    
    if category1 is not None and category2 is not None:
        total_tickets = len(category1.channels) + len(category2.channels)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f' in Tickets'))
       # print(f'Bot is watching Tickets.')
    else:
        print('One or both categories are not found, skipping presence update.')

bot.add_cog(Ticket_System(bot))
bot.add_cog(Ticket_Command(bot))
bot.run(BOT_TOKEN)

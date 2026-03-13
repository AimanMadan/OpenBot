import discord 
from discord.ext import commands 
import logging 
from config import settings

token = settings.discord_token.get_secret_value()

handler = logging.FileHandler(filename='dicord.log',
                              encoding='utf-8',
                              mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.message_content = True
intents.members = True
  

bot = commands.Bot(command_prefix='#',
                   intents=intents)

@bot.event
async def on_ready():
    print("Number One President")
    
@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to America {member.name}")
    

bot.run(token, 
        log_handler=handler,
        log_level=logging.DEBUG)
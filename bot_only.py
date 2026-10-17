import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

load_dotenv(dotenv_path='~/Workspace/AbrarAssistant/.env')
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    logging.info(f"DEBUG: Message from {message.author}: {message.content}")
    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))

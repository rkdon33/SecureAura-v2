import os
import discord
from discord.ext import commands
from keep_alive import keep_alive

TOKEN = os.environ['DISCORD_TOKEN']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents, case_insensitive=True)
bot.remove_command('help')

# MongoDB database connection
from database import db

bot.db = db
bot.log_channels = db.get_all_log_channels()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Moderating the server!"))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Load cogs
initial_extensions = [
    'cogs.security_feature',
    'cogs.moderation',
    'cogs.msg',
    'cogs.log_channel',
    'cogs.invite_log',
    'cogs.premium_security',
    'cogs.greet_pannel',
    'cogs.help'
]

async def load_extensions():
    for ext in initial_extensions:
        await bot.load_extension(ext)
    await bot.load_extension('cogs.whitelist_commands')

async def main():
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    keep_alive()  # Start the web server to keep the bot alive
    asyncio.run(main())
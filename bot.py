import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tortoise import Tortoise

# Load secrets from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("COMMAND_PREFIX", "!")
DATABASE_URL = os.getenv("DATABASE_URL")

# Setup intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"✅ Lucid Dreams is online as {bot.user}!")


# Setup the database connection
async def init_db():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["models"]}  # update these later
    )
    await Tortoise.generate_schemas()
    print("📦 Database initialized.")


# Load all command extensions
async def load_extensions():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"commands.{filename[:-3]}")
                print(f"📥 Loaded extension: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")


# Entrypoint
async def main():
    async with bot:
        await init_db()
        await load_extensions()
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped manually.")

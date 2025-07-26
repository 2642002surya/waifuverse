import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv
import discord

from tortoise import Tortoise
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Import all your cogs here
initial_extensions = [
    "commands.admin",
    "commands.battle",
    "commands.gallery",
    "commands.intimate",
]

# ----------------------------
# Database Initialization
# ----------------------------

async def init_db():
    await Tortoise.init(
        db_url=os.getenv("DATABASE_URL"),
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas()

# ----------------------------
# Bot Events
# ----------------------------

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    await init_db()

# ----------------------------
# Load Cogs
# ----------------------------

for extension in initial_extensions:
    try:
        bot.load_extension(extension)
        print(f"Loaded extension: {extension}")
    except Exception as e:
        print(f"Failed to load extension {extension}: {e}")

# ----------------------------
# Run Bot
# ----------------------------

async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())

# ----------------------------
# Render Web Service Keep-Alive
# ----------------------------

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive!')

def run_keep_alive():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_keep_alive, daemon=True).start()

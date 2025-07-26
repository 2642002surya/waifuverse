import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from discord.ext import commands
from dotenv import load_dotenv
import discord
from tortoise import Tortoise

load_dotenv()

# ----------------------------
# Intents and Bot Definition
# ----------------------------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# Initial Extensions (Cogs)
# ----------------------------
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
        modules={"models": ["models"]},
    )
    await Tortoise.generate_schemas()

# ----------------------------
# Events
# ----------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot connected as {bot.user}")
    await init_db()

# ----------------------------
# Keep-Alive Webserver (Render)
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

# Start keep-alive thread
threading.Thread(target=run_keep_alive, daemon=True).start()

# ----------------------------
# Main Entry
# ----------------------------
async def main():
    # Load extensions (cogs)
    for ext in initial_extensions:
        await bot.load_extension(ext)

    # Start the bot
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))

# Run the bot
asyncio.run(main())

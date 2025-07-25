import discord
import os
import random
import time
from discord.ext import commands
from tortoise.exceptions import DoesNotExist
from models import User, CharacterInstance, Character  # Adjust if model paths differ

name = "intimate"
description = "Interact intimately with your waifus."

SCENES = [  # [snipped for brevity] — keep your full SCENES list here.
    "🔥 As the moonlight filters through the silk curtains, **{waifu}** gently pulls you closer...",
    # ... (include all your 70+ scenes here)
]

class Intimate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # per-user cooldown tracking

    @commands.command(name='intimate', help='Have an intimate scene with one of your waifus (NSFW only)')
    async def intimate(self, ctx):
        if not ctx.channel.is_nsfw():
            return await ctx.send('❌ This command can only be used in NSFW channels.')

        user_id = ctx.author.id

        try:
            user = await User.get(discord_id=user_id).prefetch_related("waifus__character")
        except DoesNotExist:
            return await ctx.send('You must summon and own at least one waifu before doing this. Try `!summon`.')

        waifus = await user.waifus.all().prefetch_related("character")
        if not waifus:
            return await ctx.send('You must summon and own at least one waifu before doing this. Try `!summon`.')

        # Cooldown logic (3 hours)
        now = time.time()
        cooldown_period = 60 * 60 * 3
        last_used = self.cooldowns.get(user_id, 0)
        if now - last_used < cooldown_period:
            remaining = int((cooldown_period - (now - last_used)) // 60) + 1
            return await ctx.send(f'💤 You need to wait **{remaining} more minutes** before another intimate moment.')

        self.cooldowns[user_id] = now

        # Pick random waifu and character
        waifu_instance = random.choice(waifus)
        character = waifu_instance.character

        # Increment affection
        waifu_instance.affection += 5
        await waifu_instance.save()

        # Load image file (e.g. "characters/character - 1.webp")
        image_path = None
        characters_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../characters"))
        for file in os.listdir(characters_dir):
            if file.lower().startswith(character.name.lower()) and file.endswith(".webp"):
                image_path = os.path.join(characters_dir, file)
                break

        # Format scene
        scene = random.choice(SCENES).format(waifu=character.name)

        embed = discord.Embed(
            title=f"❤️ You spend a passionate moment with {character.name}",
            description=scene,
            color=0xFF69B4,
        )
        if image_path:
            embed.set_thumbnail(url=f"attachment://{os.path.basename(image_path)}")
        embed.set_footer(text="NSFW Scene - You feel closer to her now.")

        if image_path:
            await ctx.send(embed=embed, file=discord.File(image_path))
        else:
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Intimate(bot))

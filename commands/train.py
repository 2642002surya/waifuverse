name = "train"
description = "Train your waifus to improve their skills."

import discord
from discord.ext import commands
from tortoise.exceptions import DoesNotExist
from models import User, Character
import random
import time

class Train(commands.Cog):
    cooldowns = {}

    def __init__(self, bot):
        self.bot = bot
        self.cooldown_seconds = 60 * 60 * 1  # 1 hour cooldown

    @commands.command(name='train', help='Train a waifu. Usage: !train or !train <waifu name>')
    async def train(self, ctx, *, waifu_name: str = None):
        user_id = str(ctx.author.id)
        now = time.time()

        # Cooldown check
        last_train = self.cooldowns.get(user_id, 0)
        if now - last_train < self.cooldown_seconds:
            remaining = int((self.cooldown_seconds - (now - last_train)) / 60)
            return await ctx.reply(f"💤 You need to wait **{remaining} more minutes** before training again.")

        # Fetch user
        user, _ = await User.get_or_create(discord_id=user_id, defaults={"name": ctx.author.name})

        # Fetch waifus
        await user.fetch_related("waifus")
        if not user.waifus:
            return await ctx.reply("❌ You must own at least one waifu to train. Use `!summon` first.")

        # Choose waifu
        waifu = None
        if waifu_name:
            waifu = next((w for w in user.waifus if w.name.lower() == waifu_name.lower()), None)
            if not waifu:
                return await ctx.reply(f"❌ You haven't claimed any waifu named **{waifu_name}**.")
        else:
            waifu = random.choice(user.waifus)

        # Training logic
        atk_gain = random.randint(1, 5)
        hp_gain = random.randint(5, 20)
        crit_gain = 1 if random.random() < 0.25 else 0
        exp_gain = random.randint(10, 24)

        waifu.atk += atk_gain
        waifu.hp += hp_gain
        waifu.crit += crit_gain
        waifu.exp += exp_gain

        exp_needed = waifu.level * 100
        leveled_up = False
        if waifu.exp >= exp_needed:
            waifu.level += 1
            waifu.exp -= exp_needed
            waifu.hp += 50
            waifu.atk += 10
            waifu.crit += 1
            leveled_up = True

        await waifu.save()

        # Apply cooldown
        self.cooldowns[user_id] = now

        # Build embed
        description = f"**+{atk_gain} ATK**, **+{hp_gain} HP**"
        if crit_gain:
            description += ", **+1 CRIT**"
        description += f"\n🎓 Gained **{exp_gain} EXP**"

        embed = discord.Embed(
            title=f"🏋️ Training: {waifu.name}",
            description=description,
            color=0x00FF99
        )
        embed.add_field(
            name="📊 Current Stats",
            value=(f"🔺 **Level {waifu.level}**\n"
                   f"⚔️ ATK: {waifu.atk}\n"
                   f"❤️ HP: {waifu.hp}\n"
                   f"💥 CRIT: {waifu.crit}\n"
                   f"📈 EXP: {waifu.exp}/{waifu.level * 100}"),
            inline=True
        )
        embed.set_footer(
            text=f"🎉 {waifu.name} leveled up to {waifu.level}!" if leveled_up else "Train more to grow stronger!"
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Train(bot))

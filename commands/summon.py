import discord
from discord.ext import commands
from models import User, Character, CharacterTemplate
import random
import asyncio
import os
import traceback

name = "summon"
description = "Summon new waifus to join your collection."

SUMMON_COST = 10
DISCOUNT_THRESHOLD = 10

class Summon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enable_animation_delay = True

    def get_gold_reward_by_potential(self, potential: int) -> int:
        thresholds = [
            (5200, 1500), (5000, 1200), (4500, 920), (4000, 780),
            (3500, 650), (3000, 500), (2500, 300), (2000, 200),
            (1500, 100)
        ]
        for threshold, reward in thresholds:
            if potential >= threshold:
                return reward
        return 100

    def get_rarity(self, potential: int) -> str:
        if potential >= 5000:
            return "SSR 🌈✨"
        elif potential >= 4000:
            return "SR 🔥"
        elif potential >= 3000:
            return "R 🔧"
        else:
            return "N 🌿"

    @commands.command(name="summon")
    async def summon(self, ctx, amount: int = 1):
        user_id = str(ctx.author.id)

        user, _ = await User.get_or_create(discord_id=user_id, defaults={
            "name": ctx.author.name
        })

        total_cost = SUMMON_COST * amount
        if amount % DISCOUNT_THRESHOLD == 0:
            total_cost = int(total_cost * 0.9)

        if user.gems < total_cost:
            await ctx.reply(f"❌ You need {total_cost} 💎 to summon {amount} times!")
            return

        templates = await CharacterTemplate.all()
        if not templates:
            await ctx.send("⚠️ No character templates found.")
            return

        base_weight = 10000
        weights = [max(base_weight - t.potential, int(base_weight * 0.1)) for t in templates]

        user.gems -= total_cost
        await user.save()

        new_count = 0
        results = []
        rare_announcements = []
        total_gold_reward = 0
        pity_counter = user.summon_count % 20
        file, image_url = None, None

        for _ in range(amount):
            try:
                if self.enable_animation_delay and amount > 1:
                    await asyncio.sleep(1)

                force_ssr = pity_counter >= 19
                if force_ssr:
                    ssr_pool = [t for t in templates if t.potential >= 5000]
                    selected = random.choice(ssr_pool or templates)
                    pity_counter = 0
                else:
                    selected = random.choices(templates, weights=weights, k=1)[0]
                    pity_counter += 1

                name = selected.name
                pot = selected.potential
                rarity = self.get_rarity(pot)

                existing = await Character.filter(owner=user, name=name).first()

                if selected.image_path and os.path.exists(selected.image_path):
                    file = discord.File(selected.image_path, filename="waifu.webp")
                    image_url = "attachment://waifu.webp"

                if not existing:
                    await Character.create(
                        name=name,
                        level=1,
                        atk=50,
                        hp=500,
                        crit=5,
                        exp=0,
                        owner=user,
                        potential={"base": pot}
                    )
                    new_count += 1
                    results.append(f"{rarity} **{name}** (New!) — Potential: {pot}")
                else:
                    existing.atk += 10
                    existing.hp += 100
                    existing.crit = min(existing.crit + 1, 20)
                    existing.exp += 50
                    while existing.exp >= existing.level * 100:
                        existing.exp -= existing.level * 100
                        existing.level += 1
                        existing.atk += 20
                        existing.hp += 200
                        existing.crit = min(existing.crit + 1, 20)
                    await existing.save()
                    gold = self.get_gold_reward_by_potential(pot) // 2
                    user.gold += gold
                    await user.save()
                    total_gold_reward += gold
                    results.append(f"🔁 **{name}** (Duplicate) — +{gold} Gold, XP gained & Boosted Stats!")

                if rarity.startswith("SSR"):
                    rare_announcements.append(f"🎉 {ctx.author.mention} summoned an {rarity}: **{name}**!")

                user.summon_count += 1
                await user.save()

            except Exception as e:
                print(f"Summon failed: {e}")
                traceback.print_exc()

        result_text = "\n".join(results)
        if len(result_text) > 4000:
            result_text = result_text[:4000].rsplit("\n", 1)[0] + "\n...and more."

        embed = discord.Embed(
            title=f"🎴 Summon Results ({amount}x)",
            description=result_text,
            color=0xFFD700 if new_count > 0 else 0xAAAAAA
        )
        embed.set_footer(text=f"💎 Spent: {total_cost} Gems | 📦 New: {new_count} | 💰 Gold Gained: {total_gold_reward}")
        if image_url:
            embed.set_thumbnail(url=image_url)

        if file:
            await ctx.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed)

        log_channel = discord.utils.get(ctx.guild.text_channels, name="lucky-users")
        if log_channel:
            for msg in rare_announcements:
                await log_channel.send(msg)

async def setup(bot):
    await bot.add_cog(Summon(bot))

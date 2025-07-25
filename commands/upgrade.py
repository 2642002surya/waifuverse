import discord
from discord.ext import commands
from models import User, Character
from tortoise.exceptions import DoesNotExist

name = "upgrade"
description = "Feed XP to your waifu to level her up! Usage: !upgrade <waifu name> [times]"

class Upgrade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="upgrade")
    async def upgrade_waifu(self, ctx, *, waifu_input: str = None):
        if not waifu_input:
            await ctx.send("❗ Usage: `!upgrade <waifu name> [times]`")
            return

        try:
            user, _ = await User.get_or_create(discord_id=str(ctx.author.id), defaults={"name": ctx.author.name})
            waifus = await user.waifus.all()

            # Split name and optional repetition count
            parts = waifu_input.rsplit(" ", 1)
            waifu_name = parts[0]
            repeat = 1
            if len(parts) == 2 and parts[1].isdigit():
                repeat = min(int(parts[1]), 100)

            waifu = next((w for w in waifus if w.name.lower() == waifu_name.lower()), None)
            if not waifu:
                await ctx.send("❌ You haven't claimed this waifu.")
                return

            xp_gain_per_upgrade = 100
            total_xp_gained = 0
            total_gold_used = 0
            leveled_up = False

            for _ in range(repeat):
                gold_cost = waifu.level * 100
                if user.gold < gold_cost:
                    break

                xp_needed = waifu.level * 100
                user.gold -= gold_cost
                total_gold_used += gold_cost

                waifu.exp += xp_gain_per_upgrade
                total_xp_gained += xp_gain_per_upgrade

                while waifu.exp >= xp_needed:
                    waifu.exp -= xp_needed
                    waifu.level += 1
                    xp_needed = waifu.level * 100
                    waifu.atk += 20
                    waifu.hp += 200
                    waifu.crit = min(waifu.crit + 1, 20)
                    leveled_up = True

            await user.save()
            await waifu.save()

            embed = discord.Embed(
                title=f"📈 Upgraded: {waifu.name}",
                description=f"{waifu.name} received upgrades up to Level **{waifu.level}**!",
                color=0xFFD700
            )
            embed.add_field(name="🔋 Current XP", value=f"{waifu.exp} / {waifu.level * 100}", inline=True)
            embed.add_field(name="🗡️ ATK", value=str(waifu.atk), inline=True)
            embed.add_field(name="❤️ HP", value=str(waifu.hp), inline=True)
            embed.add_field(name="💥 Crit", value=str(waifu.crit), inline=True)
            embed.add_field(name="💰 Gold Left", value=f"{user.gold}", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name="📊 XP Gained", value=f"{total_xp_gained}", inline=True)
            embed.add_field(name="💸 Gold Used", value=f"{total_gold_used}", inline=True)

            if leveled_up and waifu.level >= 10:
                embed.add_field(name="✨ Evolution!", value="Your waifu is ready to evolve! (Feature coming soon)", inline=False)

            embed.set_footer(text="Use !upgrade again to level up more waifus!")
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error in upgrade command: {e}")
            await ctx.send("❌ An error occurred while upgrading your waifu.")

async def setup(bot):
    await bot.add_cog(Upgrade(bot))

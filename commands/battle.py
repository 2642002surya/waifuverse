# battle.py
name = "battle"
description = "Engage in battles with your waifus against others."

import discord
import random
import traceback
from datetime import datetime
from discord.ext import commands

from models import User, Character, Relic, BattleHistory  # Correct imports

class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def elemental_bonus(self, e1, e2):
        chart = {
            "Fire": "Earth", "Water": "Fire", "Earth": "Lightning",
            "Lightning": "Water", "Light": "Dark", "Dark": "Light"
        }
        if e1 == chart.get(e2): return -0.1
        if chart.get(e1) == e2: return 0.1
        return 0

    def health_bar(self, hp, max_hp):
        total = 20
        filled = int((hp / max_hp) * total)
        return f"[{'█' * filled}{'.' * (total - filled)}] {int(hp)}/{int(max_hp)}"

    async def get_best_waifu(self, user: User):
        waifus = await Character.filter(owner=user)
        if not waifus:
            return None
        return max(waifus, key=lambda w: w.potential or 0)

    async def get_waifu_by_name(self, user: User, name: str):
        return await Character.get_or_none(owner=user, name__iexact=name)

    async def award_xp(self, waifu: Character, amount: int):
        leveled_up = False
        waifu.exp += amount
        while waifu.exp >= waifu.level * 100 and waifu.level < 100:
            waifu.exp -= waifu.level * 100
            waifu.level += 1
            waifu.atk += 1
            waifu.hp += 5
            waifu.crit += 1
            leveled_up = True
        await waifu.save()
        return leveled_up, waifu.level

    @commands.command(name="battlereport")
    async def battlereport(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user = await User.get_or_none(discord_id=str(target.id))
        if not user:
            await ctx.send(f"{target.display_name} has no recorded battle history.")
            return

        history = await BattleHistory.filter(user=user).order_by("-timestamp").limit(5)
        if not history:
            await ctx.send(f"{target.display_name} has no recorded battle history.")
            return

        embed = discord.Embed(
            title=f"📜 Battle History: {target.display_name}",
            color=discord.Color.gold()
        )
        for entry in history:
            embed.add_field(
                name=f"{entry.waifu_name} vs {entry.opponent_name}",
                value=f"**Result:** {entry.result.capitalize()} | 🕒 {entry.timestamp.strftime('%Y-%m-%d %H:%M')} UTC",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="battle")
    async def battle(self, ctx, *, waifu_name=None):
        try:
            user = await User.get_or_none(discord_id=str(ctx.author.id)).prefetch_related("waifus", "relics")
            if not user or not await Character.filter(owner=user).exists():
                await ctx.send("You need to summon a waifu first using `!summon`.")
                return

            opponent_user = None
            if ctx.message.mentions:
                mentioned = ctx.message.mentions[0]
                if mentioned.bot or mentioned.id == ctx.author.id:
                    await ctx.send("Invalid opponent.")
                    return
                opponent_user = await User.get_or_none(discord_id=str(mentioned.id))
                if not opponent_user or not await Character.filter(owner=opponent_user).exists():
                    await ctx.send("Opponent has no waifus.")
                    return
            else:
                all_users = await User.all().prefetch_related("waifus")
                candidates = [u for u in all_users if u.discord_id != str(ctx.author.id) and u.waifus]
                opponent_user = random.choice(candidates) if candidates else None

            w1 = await self.get_waifu_by_name(user, waifu_name) if waifu_name else await self.get_best_waifu(user)
            w2 = await self.get_best_waifu(opponent_user) if opponent_user else await Character.get_random_bot_waifu()

            if not w1 or not w2:
                await ctx.send("❌ Could not load one of the waifus.")
                return

            relic1 = await Relic.get_or_none(owner=user, assigned_to=w1.name)
            relic2 = await Relic.get_or_none(owner=opponent_user, assigned_to=w2.name) if opponent_user else None

            def relic_boost(r: Relic):
                return (r.atk_boost or 0, r.hp_boost or 0, r.crit_boost or 0) if r else (0, 0, 0)

            atk1b, hp1b, _ = relic_boost(relic1)
            atk2b, hp2b, _ = relic_boost(relic2)

            max_hp1 = hp1 = 1000 + (w1.potential or 0) / 2 + hp1b
            max_hp2 = hp2 = 1000 + (w2.potential or 0) / 2 + hp2b

            bonus1 = self.elemental_bonus(w1.element, w2.element)
            bonus2 = self.elemental_bonus(w2.element, w1.element)
            battle_log = []
            round_num = 1

            while hp1 > 0 and hp2 > 0 and round_num <= 10:
                dmg1 = int(random.uniform(0, 100) + (w1.potential or 0) * 0.05 + bonus1 * 20 + atk1b)
                dmg2 = int(random.uniform(0, 100) + (w2.potential or 0) * 0.05 + bonus2 * 20 + atk2b)
                crit1 = random.random() < (w1.crit or 0) / 100
                crit2 = random.random() < (w2.crit or 0) / 100
                if crit1: dmg1 = int(dmg1 * 1.5)
                if crit2: dmg2 = int(dmg2 * 1.5)
                hp2 -= dmg1
                hp1 -= dmg2

                battle_log.append(
                    f"**Round {round_num}**\n"
                    f"{w1.name} dealt **{dmg1}**{' 💥' if crit1 else ''} | {self.health_bar(hp2, max_hp2)}\n"
                    f"{w2.name} dealt **{dmg2}**{' 💥' if crit2 else ''} | {self.health_bar(hp1, max_hp1)}"
                )
                round_num += 1

            result_text = ""
            xp = 20
            timestamp = datetime.utcnow()

            if hp1 <= 0 and hp2 <= 0:
                result_text = "💥 It's a draw!"
                await self.award_xp(w1, xp)
                if w2: await self.award_xp(w2, xp)
                result1, result2 = "draw", "draw"
            elif hp1 > hp2:
                result_text = f"🏆 **{ctx.author.display_name}**'s **{w1.name}** wins!"
                up, lv = await self.award_xp(w1, xp)
                if up: result_text += f" 🎉 Level up to **{lv}**!"
                user.gold += 100
                result1, result2 = "win", "lose"
            else:
                result_text = f"🏆 **{opponent_user.discord_name if opponent_user else 'Bot'}**'s **{w2.name}** wins!"
                if w2:
                    up, lv = await self.award_xp(w2, xp)
                    if up: result_text += f" 🎉 Level up to **{lv}**!"
                    opponent_user.gold += 100
                result1, result2 = "lose", "win"

            await user.save()
            if opponent_user:
                await opponent_user.save()

            # Record history
            await BattleHistory.create(user=user, waifu_name=w1.name, opponent_name=w2.name, result=result1, timestamp=timestamp)
            if opponent_user:
                await BattleHistory.create(user=opponent_user, waifu_name=w2.name, opponent_name=w1.name, result=result2, timestamp=timestamp)

            embed = discord.Embed(title="⚔️ Battle Report", color=discord.Color.red())
            embed.description = f"**{w1.name}** ({w1.element}) vs **{w2.name}** ({w2.element})\n\n" + "\n\n".join(battle_log) + f"\n\n{result_text}"
            embed.set_footer(text=f"Power: {w1.potential} vs {w2.potential}")
            await ctx.send(embed=embed)
        except Exception as e:
            traceback.print_exc()
            await ctx.send("⚠️ Unexpected error occurred during battle.")

async def setup(bot):
    await bot.add_cog(Battle(bot))

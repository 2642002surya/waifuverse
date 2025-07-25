import asyncio
import discord
from discord.ext import commands
from tortoise.exceptions import DoesNotExist
from models import User, Character
import os
import json
import time

CHAR_PER_PAGE = 10

def xp_bar(xp, level):
    xp_needed = level * 100
    progress = int((xp / xp_needed) * 10) if xp_needed > 0 else 0
    return "▰" * progress + "▱" * (10 - progress)

def get_potential_score(potential):
    if isinstance(potential, dict):
        return sum(potential.values())
    return 0

class NavigationButton(discord.ui.Button):
    def __init__(self, label, direction):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        view: ProfileView = self.view
        view.page += self.direction
        view.update_buttons()
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class SortButton(discord.ui.Button):
    def __init__(self, label, sort_by):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.sort_by = sort_by

    async def callback(self, interaction: discord.Interaction):
        view: ProfileView = self.view
        if view.sort_by != self.sort_by:
            view.sort_by = self.sort_by
            view.sort_waifus()
            view.page = 0
            view.update_buttons()
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class ProfileView(discord.ui.View):
    def __init__(self, user_id, waifus, characters_dir, sort_by="potential", page=0):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.waifus_raw = waifus
        self.characters_dir = characters_dir
        self.sort_by = sort_by
        self.page = page
        self.per_page = CHAR_PER_PAGE
        self.sort_waifus()
        self.update_buttons()

    def sort_waifus(self):
        if self.sort_by == "level":
            self.waifus = sorted(self.waifus_raw, key=lambda w: w.level, reverse=True)
        else:
            self.waifus = sorted(self.waifus_raw, key=lambda w: get_potential_score(w.potential), reverse=True)
        self.max_page = max(0, (len(self.waifus) - 1) // self.per_page)

    def update_buttons(self):
        self.clear_items()
        if self.page > 0:
            self.add_item(NavigationButton("◀️ Prev", direction=-1))
        if self.page < self.max_page:
            self.add_item(NavigationButton("▶️ Next", direction=1))
        self.add_item(SortButton("Sort by Potential", "potential"))
        self.add_item(SortButton("Sort by Level", "level"))

    def get_embed(self):
        embed = discord.Embed(
            title=f"📝 Your Waifus (Sorted by {self.sort_by.title()})",
            color=discord.Color.pink()
        )
        start = self.page * self.per_page
        end = start + self.per_page
        waifu_list = self.waifus[start:end]
        for i, w in enumerate(waifu_list, start=start + 1):
            embed.add_field(
                name=f"{i}. {w.name}",
                value=f"Lvl {w.level} | ❤️ {w.hp} HP | ⚔️ {w.atk} ATK",
                inline=False
            )
        embed.set_footer(text=f"Page {self.page + 1}/{self.max_page + 1}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.characters_dir = 'characters'

    @commands.command(name="profile")
    async def profile(self, ctx, sort_by="potential"):
        try:
            user = await User.get(discord_id=str(ctx.author.id)).prefetch_related("waifus")
        except DoesNotExist:
            await ctx.send("❌ You don't have a profile yet.")
            return

        waifus = await user.waifus.all()
        if not waifus:
            await ctx.send("😢 You haven't claimed any waifus yet.")
            return

        profile_embed = discord.Embed(
            title=f"💫 {user.name}'s Profile",
            description="Your NSFW RPG journey so far...",
            color=0xFFC0CB
        )
        profile_embed.add_field(name="💰 Gold", value=str(user.gold), inline=True)
        profile_embed.add_field(name="💎 Gems", value=str(user.gems), inline=True)
        profile_embed.add_field(name="🌸 Claimed Waifus", value=str(len(waifus)), inline=True)
        profile_embed.add_field(name="❤️ Affection", value=str(user.affection), inline=True)
        profile_embed.add_field(name="🧪 Summons Used", value=str(user.summon_count), inline=True)
        profile_embed.add_field(name="📈 Level / XP", value=f"Lvl {user.level} / {user.xp} XP", inline=True)

        relics = [w.relic for w in waifus if w.relic]
        if relics:
            profile_embed.add_field(name="🗡️ Equipped Relics", value=", ".join(set(relics)), inline=False)

        await ctx.send(embed=profile_embed)

        view = ProfileView(ctx.author.id, waifus, self.characters_dir, sort_by=sort_by)
        await ctx.send(embed=view.get_embed(), view=view)

    @commands.command(name="characters")
    async def character_count(self, ctx):
        if not os.path.exists(self.characters_dir):
            await ctx.send("❌ Characters directory not found.")
            return
        count = len([f for f in os.listdir(self.characters_dir) if f.endswith(".json")])
        await ctx.send(f"📖 Total characters in bot: **{count}**")

async def setup(bot):
    await bot.add_cog(Profile(bot))

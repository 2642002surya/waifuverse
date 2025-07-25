import discord
from discord.ext import commands
import os
import json
import random
from tortoise.exceptions import DoesNotExist
from models import User, Character, Relic

class Relics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.relics_dir = os.path.join("store", "weapons")

    def get_relic_files(self):
        return [f for f in os.listdir(self.relics_dir) if f.endswith(".json")]

    def load_relic(self, filename):
        with open(os.path.join(self.relics_dir, filename), "r", encoding="utf-8") as f:
            return json.load(f)

    @commands.command(name="assignrelic")
    async def assign_relic(self, ctx, relic_name: str, waifu_name: str):
        user = await User.get(discord_id=str(ctx.author.id)).prefetch_related("relics", "waifus")
        relic = next((r for r in await user.relics.all() if r.name.lower() == relic_name.lower()), None)
        waifu = next((w for w in await user.waifus.all() if w.name.lower() == waifu_name.lower()), None)

        if not relic:
            return await ctx.send("❌ Relic not found in your inventory.")
        if not waifu:
            return await ctx.send("❌ Waifu not found.")

        waifu.relic = relic
        await waifu.save()
        await ctx.send(f"✅ Assigned **{relic_name}** to **{waifu_name}**.")

    @commands.command(name="relicsummon")
    async def relic_summon(self, ctx, amount: int = 1):
        user = await User.get(discord_id=str(ctx.author.id))

        if user.level < 60:
            return await ctx.send("🔒 Relics unlock at level 60!")
        cost = 50 * amount
        if user.diamonds < cost:
            return await ctx.send(f"❌ You need {cost} diamonds.")

        relic_files = self.get_relic_files()
        pulled = []

        for _ in range(amount):
            filename = random.choice(relic_files)
            relic_data = self.load_relic(filename)

            relic = await Relic.create(
                name=relic_data["name"],
                quality=relic_data["quality"],
                attributes=relic_data.get("attributes", []),
                image=relic_data.get("image", ""),
                level=1,
                awaken=0,
                owner=user
            )
            pulled.append(relic)

        user.diamonds -= cost
        await user.save()

        embed = discord.Embed(title=f"🔮 Relic Summon x{amount}", color=0x55ffff)
        for relic in pulled:
            embed.add_field(name=f"{relic.quality} ⭐ {relic.name}", value="Relic summoned!", inline=False)
            if relic.image:
                embed.set_thumbnail(url=f"attachment://{relic.image}")
        await ctx.send(embed=embed)

    @commands.command(name="relicupgrade")
    async def relic_upgrade(self, ctx, name: str):
        user = await User.get(discord_id=str(ctx.author.id)).prefetch_related("relics")
        relics = [r for r in await user.relics.all() if r.name.lower() == name.lower()]

        if len(relics) < 2:
            return await ctx.send("❌ You need at least 2 of the same relic to upgrade.")

        base = relics[0]
        await relics[1].delete()
        base.level += 1
        if "+" not in base.quality:
            base.quality += "+"
        await base.save()
        await ctx.send(f"✅ {name} upgraded to Level {base.level}!")

    @commands.command(name="relicinherit")
    async def relic_inherit(self, ctx, from_name: str, to_name: str, inherit_type: str):
        user = await User.get(discord_id=str(ctx.author.id)).prefetch_related("relics")
        if user.diamonds < 100:
            return await ctx.send("❌ You need 100 diamonds for inheritance.")

        relics = await user.relics.all()
        from_relic = next((r for r in relics if r.name.lower() == from_name.lower()), None)
        to_relic = next((r for r in relics if r.name.lower() == to_name.lower()), None)

        if not from_relic or not to_relic:
            return await ctx.send("❌ Relic(s) not found.")

        if inherit_type == "quality":
            to_relic.quality = from_relic.quality
        elif inherit_type == "awaken" and user.level >= 110:
            to_relic.awaken = from_relic.awaken
        else:
            return await ctx.send("❌ Invalid type or conditions not met.")

        user.diamonds -= 100
        await user.save()
        await to_relic.save()
        await ctx.send(f"🔁 Inherited {inherit_type} from {from_name} to {to_name}.")

    @commands.command(name="relicawaken")
    async def relic_awaken(self, ctx, name: str):
        user = await User.get(discord_id=str(ctx.author.id)).prefetch_related("relics")
        relic = next((r for r in await user.relics.all() if r.name.lower() == name.lower()), None)

        if not relic:
            return await ctx.send("❌ Relic not found.")

        level = relic.level
        cost = [100, 150, 200]
        tier = 0 if level >= 90 else 1 if level >= 60 else 2 if level >= 30 else -1

        if tier == -1:
            return await ctx.send("⚠️ Relic must be at least level 30 to awaken.")
        if user.resonance_crystals < cost[tier]:
            return await ctx.send(f"❌ You need {cost[tier]} resonance crystals.")

        relic.awaken += 1
        user.resonance_crystals -= cost[tier]
        await user.save()
        await relic.save()
        await ctx.send(f"✨ {name} awakened to level {relic.awaken}!")

    @commands.command(name="relics")
    async def relics_overview(self, ctx):
        embed = discord.Embed(
            title="🗡️ Relic Commands",
            description=(
                "**!relicsummon** - Summon a relic using diamonds\n"
                "**!relicupgrade <name>** - Upgrade relic with duplicate\n"
                "**!relicinherit <from> <to> <quality|awaken>** - Inherit relic traits\n"
                "**!relicawaken <name>** - Awaken relic using resonance crystals\n"
                "**!assignrelic <relic> <waifu>** - Assign relic to waifu"
            ),
            color=0x88ccff
        )
        await ctx.send(embed=embed)

    @commands.command(name="myrelics")
    async def my_relics(self, ctx):
        user = await User.get(discord_id=str(ctx.author.id)).prefetch_related("relics")
        relics = await user.relics.all()
        if not relics:
            return await ctx.send("🪨 You don't own any relics yet.")

        embed = discord.Embed(title="🧿 Your Relics", color=0x88ccff)
        for relic in relics:
            attrs = ", ".join(f"{a['type']} +{a['value']}" for a in relic.attributes)
            embed.add_field(
                name=f"{relic.quality} ⭐ {relic.name} (Lv{relic.level})",
                value=f"{attrs or 'No attributes'} | Awaken: {relic.awaken}",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Relics(bot))

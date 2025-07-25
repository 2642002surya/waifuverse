import discord
from discord.ext import commands
from tortoise.exceptions import DoesNotExist
from models import User, Character, Relic
import asyncio
import json
import os

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_id = 1344603209829974016  # Replace with your Discord ID

    def is_admin(self, ctx):
        return ctx.author.id == self.admin_id

    @commands.command(name="give", help="Give gold or gems to a user. Admin only.")
    async def give(self, ctx, amount: int, currency: str, member: discord.Member):
        if not self.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        currency = currency.lower()
        if currency not in ["gold", "gems"]:
            return await ctx.send("❌ Currency must be either 'gold' or 'gems'.")

        user, _ = await User.get_or_create(discord_id=member.id, defaults={"name": member.name})
        setattr(user, currency, getattr(user, currency) + amount)
        await user.save()

        await ctx.send(f"✅ Given {amount} {currency} to {member.mention}.")

    @commands.command(name="erase", help="Erase all messages in this channel. Admin only.")
    async def erase(self, ctx):
        if not self.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        await ctx.send("🧹 Erasing all messages in this channel...", delete_after=3)

        def not_pinned(msg): return not msg.pinned
        deleted = await ctx.channel.purge(limit=None, check=not_pinned)

        await ctx.send(f"✅ Erased {len(deleted)} messages (excluding pinned).", delete_after=5)

    @commands.command(name="reset_profiles", help="Reset all user profiles. Admin only.")
    async def reset_profiles(self, ctx):
        if not self.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        confirm_msg = await ctx.send("⚠️ Are you sure you want to reset all user profiles? React with ✅ to confirm.")
        await confirm_msg.add_reaction("✅")

        def check(reaction, user):
            return user.id == self.admin_id and str(reaction.emoji) == "✅" and reaction.message.id == confirm_msg.id

        try:
            await self.bot.wait_for("reaction_add", timeout=15.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("❌ Reset canceled due to timeout.")

        await User.all().update(gold=500, gems=50, affection=0, level=1, xp=0)
        await Character.all().delete()

        await ctx.send("✅ All user profiles have been reset to default.")

    @commands.command(name="banwaifu", help="Remove a specific waifu from a user. Admin only.")
    async def banwaifu(self, ctx, member: discord.Member, *, waifu_name: str):
        if not self.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        try:
            user = await User.get(discord_id=member.id)
        except DoesNotExist:
            return await ctx.send("❌ User not found.")

        deleted_count = await Character.filter(user=user, name__iexact=waifu_name).delete()
        if deleted_count == 0:
            return await ctx.send(f"❌ {member.display_name} does not have a waifu named '{waifu_name}'.")
        
        await ctx.send(f"✅ Removed **{waifu_name}** from {member.mention}'s waifu list.")

    @commands.command(name="viewdata", help="View raw user data for debugging. Admin only.")
    async def viewdata(self, ctx, member: discord.Member):
        if not self.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        try:
            user = await User.get(discord_id=member.id).prefetch_related("waifus")
        except DoesNotExist:
            return await ctx.send("❌ This user has no profile.")

        waifus = await Character.filter(user=user).values()
        data = {
            "discord_id": user.discord_id,
            "name": user.name,
            "gold": user.gold,
            "gems": user.gems,
            "affection": user.affection,
            "level": user.level,
            "xp": user.xp,
            "waifus": waifus,
        }

        raw = json.dumps(data, indent=2)
        if len(raw) > 1900:
            with open("temp_user_data.json", "w", encoding="utf-8") as f:
                f.write(raw)
            await ctx.send("📦 Data too large, sending as file.")
            await ctx.send(file=discord.File("temp_user_data.json"))
            os.remove("temp_user_data.json")
        else:
            await ctx.send(f"```json\n{raw}\n```")

    @commands.command(name="setlevel", help="Set a user's level. Admin only.")
    async def setlevel(self, ctx, member: discord.Member, level: int):
        if not self.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        user, _ = await User.get_or_create(discord_id=member.id, defaults={"name": member.name})
        user.level = level
        user.xp = 0
        await user.save()

        await ctx.send(f"✅ Set {member.mention}'s level to {level}.")

    @commands.command(name="resetuser", help="Reset a specific user's profile. Admin only.")
    async def resetuser(self, ctx, member: discord.Member):
        if not self.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        user, _ = await User.get_or_create(discord_id=member.id, defaults={"name": member.name})
        user.gold = 500
        user.gems = 50
        user.affection = 0
        user.level = 1
        user.xp = 0
        await user.save()

        await Character.filter(user=user).delete()
        await ctx.send(f"✅ Reset profile for {member.mention}.")

    @commands.command(name="setlevel")
    async def setlevel(self, ctx, member: discord.Member, level: int):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized.")

        user, _ = await User.get_or_create(discord_id=member.id)
        user.level = level
        await user.save()
        await ctx.send(f"✅ {member.name}'s level set to {level}.")

    @commands.command(name="viewdata")
    async def viewdata(self, ctx, member: discord.Member):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized.")

        try:
            user = await User.get(discord_id=member.id).prefetch_related("waifus", "relics")
            data = {
                "discord_id": user.discord_id,
                "level": user.level,
                "xp": user.xp,
                "gold": user.gold,
                "gems": user.gems,
                "affection": user.affection,
                "waifus": [w.name for w in user.waifus],
                "relics": [r.name for r in user.relics],
            }
            content = json.dumps(data, indent=2)
            await ctx.send(f"📦 User data for `{member.name}`:\n```json\n{content[:1900]}```")
        except DoesNotExist:
            await ctx.send("❌ User not found.")

    @commands.command(name="banwaifu")
    async def banwaifu(self, ctx, member: discord.Member, *, waifu_name: str):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized.")

        try:
            user = await User.get(discord_id=member.id)
            waifu = await Character.get(name__iexact=waifu_name, user=user)
            await waifu.delete()
            await ctx.send(f"❌ Removed `{waifu_name}` from {member.name}.")
        except DoesNotExist:
            await ctx.send("❌ User or waifu not found.")

    @commands.command(name="editxp")
    async def editxp(self, ctx, member: discord.Member, amount: int):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized.")

        user, _ = await User.get_or_create(discord_id=member.id)
        user.xp += amount
        await user.save()
        await ctx.send(f"✅ Edited XP by {amount} for {member.name}.")

    @commands.command(name="editaffection")
    async def editaffection(self, ctx, member: discord.Member, amount: int):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized.")

        user, _ = await User.get_or_create(discord_id=member.id)
        user.affection += amount
        await user.save()
        await ctx.send(f"💖 Affection changed by {amount} for {member.name}.")

    @commands.command(name="addrelic")
    async def addrelic(self, ctx, member: discord.Member, *, relic_name: str):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized.")

        relic_path = f"store/weapons/{relic_name}.json"
        if not os.path.exists(relic_path):
            return await ctx.send("❌ Relic not found.")

        with open(relic_path, 'r', encoding='utf-8') as f:
            relic_data = json.load(f)

        user, _ = await User.get_or_create(discord_id=member.id)

        await Character.create(user=user, **relic_data)
        await ctx.send(f"⚔️ {relic_name} has been added to {member.name}.")

    @commands.command(name="addwaifu")
    async def addwaifu(self, ctx, member: discord.Member, *, waifu_name: str):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized.")

        waifu_path = f"store/characters/{waifu_name}.json"
        if not os.path.exists(waifu_path):
            return await ctx.send("❌ Waifu not found.")

        with open(waifu_path, 'r', encoding='utf-8') as f:
            waifu_data = json.load(f)

        user, _ = await User.get_or_create(discord_id=member.id)

        await Character.create(user=user, **waifu_data)
        await ctx.send(f"✨ {waifu_name} has been added to {member.name}.")

    @commands.command(name="adminhelp")
    async def adminhelp(self, ctx):
        if ctx.author.id != self.admin_id:
            return await ctx.send("❌ You are not authorized to use this command.")

        embed = discord.Embed(
            title="🛠️ Admin Commands Panel",
            description="Here is a list of all available admin commands:",
            color=discord.Color.gold()
        )

        embed.add_field(name="💰 Currency Commands", value=(
            "`!give <amount> <gold/gems> @user`\n"
            "`!giveall <gold/gems> <amount>`"
        ), inline=False)

        embed.add_field(name="📊 User Profile Controls", value=(
            "`!setlevel @user <level>`\n"
            "`!reset_profiles`\n"
            "`!resetuser @user`\n"
            "`!viewdata @user`"
        ), inline=False)

        embed.add_field(name="💔 Waifu Management", value="`!banwaifu @user <waifu_name>`", inline=False)

        embed.add_field(name="🧹 Channel Utilities", value="`!erase`", inline=False)

        embed.add_field(name="💰 Currency & Stats", value=(
            "`!editxp @user <amount>`\n"
            "`!editaffection @user <amount>`"
        ), inline=False)

        embed.add_field(name="👥 Waifu & Relic Management", value=(
            "`!addwaifu @user <waifu_name>`\n"
            "`!addrelic @user <relic_name>`"
        ), inline=False)

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="⚠️ These commands are restricted to authorized admin only.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))

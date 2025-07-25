name = "help"
description = "Show this help message or info about a specific command."

import discord
import os
import importlib.util
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_dir = os.path.dirname(__file__)
        self.prefix = bot.command_prefix if isinstance(bot.command_prefix, str) else '!'

    @commands.command(name='help', help='Shows a list of all commands or info about a specific one.')
    async def help(self, ctx, *, arg=None):
        is_admin = ctx.author.guild_permissions.administrator

        command_files = [
            f for f in os.listdir(self.commands_dir)
            if f.endswith('.py') and f != '__init__.py' and (is_admin or f != 'admin.py')
        ]

        if arg:
            name = arg.lower()
            command_file = next((f for f in command_files if f.replace('.py', '') == name), None)
            if not command_file:
                return await ctx.send(f"❌ No command found with the name `{name}`.")

            embed = await self.load_help_embed(command_file, ctx, name)
            if embed:
                return await ctx.send(embed=embed)
            else:
                return await ctx.send(f"⚠️ Couldn't load help for `{name}`.")
        else:
            embed = discord.Embed(
                title='🎮 NSFW RPG Command List',
                description='Here are the available commands:',
                color=0xff6699
            )
            for file in command_files:
                module_info = await self.get_command_info(file)
                if module_info:
                    cmd_name, cmd_desc = module_info
                    embed.add_field(
                        name=f"🔹 `{self.prefix}{cmd_name}`",
                        value=cmd_desc,
                        inline=False
                    )

            embed.set_footer(text=f"Use {self.prefix}help <command> for more details.")
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            await ctx.send(embed=embed)

    async def load_help_embed(self, file, ctx, name):
        try:
            path = os.path.join(self.commands_dir, file)
            spec = importlib.util.spec_from_file_location(name, path)
            if not spec or not spec.loader:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            cmd_name = getattr(module, 'name', name)
            cmd_desc = getattr(module, 'description', 'No description provided.')

            embed = discord.Embed(
                title=f"📘 Help: `{self.prefix}{cmd_name}`",
                description=cmd_desc,
                color=0x1abc9c
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            return embed
        except Exception as e:
            print(f"[ERROR] Failed to load command help for {file}: {e}")
            return None

    async def get_command_info(self, file):
        try:
            name = file.replace('.py', '')
            path = os.path.join(self.commands_dir, file)
            spec = importlib.util.spec_from_file_location(name, path)
            if not spec or not spec.loader:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cmd_name = getattr(module, 'name', name)
            cmd_desc = getattr(module, 'description', 'No description.')
            return cmd_name, cmd_desc
        except Exception as e:
            print(f"[ERROR] Could not parse help info from {file}: {e}")
            return None

async def setup(bot):
    await bot.add_cog(Help(bot))

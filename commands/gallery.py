# commands/gallery.py
import discord
import os
from discord.ext import commands
from models import User, ClaimedWaifu  # Assuming these models are defined
from tortoise.exceptions import DoesNotExist
import json

class GalleryImageView(discord.ui.View):
    def __init__(self, character, waifu_name, user_id, characters_dir):
        super().__init__(timeout=180)
        self.character = character
        self.waifu_name = waifu_name
        self.user_id = user_id
        self.characters_dir = characters_dir
        self.index = 0
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.index > 0:
            self.add_item(discord.ui.Button(label="⬅️ Previous", style=discord.ButtonStyle.secondary, custom_id="prev"))
        if self.index < len(self.character["gallery"]) - 1:
            self.add_item(discord.ui.Button(label="➡️ Next", style=discord.ButtonStyle.secondary, custom_id="next"))

        for child in self.children:
            child.callback = self.button_callback

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your gallery session.", ephemeral=True)
            return

        if interaction.data["custom_id"] == "next":
            self.index += 1
        elif interaction.data["custom_id"] == "prev":
            self.index -= 1

        self.index = max(0, min(self.index, len(self.character["gallery"]) - 1))
        self.update_buttons()

        title = self.character["gallery"][self.index]
        image_filename = f"{self.waifu_name.lower()} - {self.index + 1}.webp"
        image_path = os.path.join(self.characters_dir, image_filename)

        embed = discord.Embed(
            title=f"💗 {self.character.get('name')} - {title}",
            description=f"📸 Outfit {self.index + 1} of {len(self.character['gallery'])}",
            color=0xFF69B4
        )

        if os.path.exists(image_path):
            file = discord.File(image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        else:
            embed.description += "\n⚠️ Image not found."
            await interaction.response.edit_message(embed=embed, attachments=[], view=self)

class WaifuSelectView(discord.ui.View):
    def __init__(self, waifus, user_id, characters_dir):
        super().__init__(timeout=120)
        self.waifus = waifus
        self.user_id = user_id
        self.characters_dir = characters_dir

        for i, waifu in enumerate(waifus, start=1):
            self.add_item(discord.ui.Button(label=f"{i}. {waifu}", style=discord.ButtonStyle.primary, custom_id=str(i)))

        for child in self.children:
            child.callback = self.waifu_callback

    async def waifu_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu.", ephemeral=True)
            return

        index = int(interaction.data["custom_id"]) - 1
        waifu_name = self.waifus[index]
        char_file = os.path.join(self.characters_dir, f"{waifu_name}.json")

        if not os.path.exists(char_file):
            await interaction.response.send_message(f"⚠️ Data for {waifu_name} not found.", ephemeral=True)
            return

        with open(char_file, 'r', encoding='utf-8') as f:
            character = json.load(f)

        if not character.get("gallery"):
            await interaction.response.send_message(f"❌ No gallery entries found for {waifu_name}.", ephemeral=True)
            return

        title = character["gallery"][0]
        image_filename = f"{waifu_name.lower()} - 1.webp"
        image_path = os.path.join(self.characters_dir, image_filename)

        embed = discord.Embed(
            title=f"💗 {character.get('name')} - {title}",
            description=f"📸 Outfit 1 of {len(character['gallery'])}",
            color=0xFF69B4
        )

        view = GalleryImageView(character, waifu_name, interaction.user.id, self.characters_dir)

        if os.path.exists(image_path):
            file = discord.File(image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            await interaction.response.edit_message(embed=embed, attachments=[file], view=view)
        else:
            embed.description += "\n⚠️ Image not found."
            await interaction.response.edit_message(embed=embed, attachments=[], view=view)

class Gallery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.characters_dir = os.path.join(os.path.dirname(__file__), '../characters')

    @commands.command(name='gallery', help='Display your unlocked waifu gallery')
    async def gallery(self, ctx):
        user_id = str(ctx.author.id)

        try:
            user = await User.get(discord_id=user_id).prefetch_related('claimed_waifus')
        except DoesNotExist:
            await ctx.send('❌ You haven’t claimed any waifus yet! Use `!summon` to get started.')
            return

        waifu_names = [waifu.character_name for waifu in user.claimed_waifus]

        if not waifu_names:
            await ctx.send('❌ No claimed waifus found.')
            return

        view = WaifuSelectView(waifu_names, ctx.author.id, self.characters_dir)
        await ctx.send("📚 **Choose a waifu to view their gallery:**", view=view)

async def setup(bot):
    await bot.add_cog(Gallery(bot))

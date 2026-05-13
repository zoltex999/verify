import discord
from discord.ext import commands


class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="soutien", description="Soutiens le bot")
    async def premium_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Soutien",
            description="Soutiens le bot via le bouton ci-dessous",
            color=discord.Color.gold(),
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Ko-fi",
                url="https://ko-fi.com/s/241a789cb1",
            )
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PremiumCog(bot))

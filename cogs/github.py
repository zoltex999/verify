import discord
from discord.ext import commands


class GithubCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="github", description="Github de Verify")
    async def github_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Github",
            description="Retrouve le code source du bot sur Github",
            color=discord.Color.blue(),
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Github",
                url="https://github.com/zoltex999/verify",
            )
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GithubCog(bot))

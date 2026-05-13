import discord
from discord.ext import commands
import sys
from .definitions import OWNER_USER_ID, BOT_STARTED_AT

class BotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="info", description="Affiche les informations du bot")
    async def show_bot_info(self, interaction: discord.Interaction):
        def build_bot_info_embed() -> discord.Embed:
            servers = len(self.bot.guilds)
            users = len(set(self.bot.get_all_members()))
            commands_list = sorted(command.name for command in self.bot.tree.get_commands())
            description_lines = [
                f"Développeur : <@{OWNER_USER_ID}>",
                f"ID : {self.bot.user.id if self.bot.user else 'Inconnu'}",
                f"Ping : {round(self.bot.latency * 1000)} ms",
                f"Serveurs : {servers}",
                f"Utilisateurs : {users}",
                f"Démarré : <t:{BOT_STARTED_AT}:R>",
                f"Python : {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                f"discord.py : {discord.__version__}",
            ]
            return discord.Embed(
                title="Verify",
                description="\n".join(description_lines),
                color=discord.Color.blurple(),
            )

        await interaction.response.send_message(embed=build_bot_info_embed(), ephemeral=True)


async def setup(bot):
    await bot.add_cog(BotCog(bot))

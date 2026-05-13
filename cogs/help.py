import discord
from discord.ext import commands
from .definitions import is_owner_user


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def build_help_embed(self, is_owner: bool) -> discord.Embed:
        commands_lines = [
            "</help:1498011116872274112> - Liste toutes les commandes disponibles",            
            "</verifier:1494600343512678564> - Lance la vérification en message privé",
            "</soutien:1504124829694165022> - Soutiens le bot",
            "</ia:1498415156471005414> - Pose une question IA sur le bot",
            "</info:1504131597270778018> - Informations du bot",
            "[ADMIN] </configurer:1496497140212432896> - Configure le rôle et le salon de vérification",
            "[DEV] </restart:1504132749949145179> - Relance le bot",
            "[DEV] </off:1504131597270778019> - Eteint le bot"
        ]

        return discord.Embed(
            title="Aide",
            description="\n".join(commands_lines),
            color=discord.Color.blurple(),
        )

    @discord.app_commands.command(name="help", description="Affiche toutes les commandes disponibles")
    async def help_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=self.build_help_embed(is_owner_user(interaction.user.id))
        )


async def setup(bot):
    await bot.add_cog(HelpCog(bot))

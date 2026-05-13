import discord
from discord.ext import commands
import os
import sys
from .definitions import is_owner_user, build_error_embed, build_success_embed


class RelancerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="restart", description="Relance le bot")
    async def restart_cmd(self, interaction: discord.Interaction):
        if not is_owner_user(interaction.user.id):
            await interaction.response.send_message(
                embed=build_error_embed("Tu n'as pas la permission d'utiliser cette commande"),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=build_success_embed("Relancement", "Le bot est en train de redémarrer..."),
            ephemeral=True,
        )
        await self.bot.close()
        os.execv(sys.executable, [sys.executable, *sys.argv])


async def setup(bot):
    await bot.add_cog(RelancerCog(bot))

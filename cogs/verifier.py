import discord
from discord.ext import commands
from .definitions import (
    ERROR_TITLE, get_verified_role, get_verify_channel_id, get_verified_role_id,
    notify_owner, send_captcha_dm
)


class VerifierCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="verifier", description="Verification humaine en message privé")
    async def verifier(self, interaction: discord.Interaction):
        if interaction.guild is None:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description="Cette commande doit être utilisée dans un serveur",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(
                embed=embed,
            )
            return

        member = interaction.user if isinstance(interaction.user, discord.Member) else interaction.guild.get_member(interaction.user.id)
        verified_role = get_verified_role(interaction.guild)
        if member and verified_role and verified_role in member.roles:
            embed = discord.Embed(
                title="<:verify:1494667945505456159> Déjà vérifié",
                description="Tu es déjà vérifié sur ce serveur",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
            return

        channel_id = get_verify_channel_id(interaction.guild.id)
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel is None:
                await notify_owner(
                    interaction.guild,
                    f"Le salon de vérification https://discord.com/channels/{interaction.guild.id}/{channel_id} est introuvable"
                    f"Reconfigure-le avec </configurer:1494600343512678564>",
                )
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=ERROR_TITLE,
                        description=(
                            "Le salon de vérification est mal configuré"
                        ),
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
                return
            if interaction.channel_id != channel_id:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=ERROR_TITLE,
                        description=f"Tu dois utiliser cette commande dans {channel.mention}",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
                return

        role_id = get_verified_role_id(interaction.guild.id)
        if not role_id or interaction.guild.get_role(role_id) is None:
            await notify_owner(
                interaction.guild,
                "Aucun rôle de vérification n'est configuré"
                "Reconfigure-le avec </configurer:1494600343512678564>",
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=ERROR_TITLE,
                    description=(
                        "La vérification n'est pas correctement configurée"
                    ),
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return

        try:
            embed_serveur = discord.Embed(
                  title="Vérification",
                description="Une vérification t'a été envoyée en message privé",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed_serveur, ephemeral=True)
            await send_captcha_dm(interaction.user, interaction.guild, self.bot)

        except discord.Forbidden:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description="Messages privés désactivés",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(VerifierCog(bot))

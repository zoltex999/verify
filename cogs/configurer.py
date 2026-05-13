import discord
from discord.ext import commands
from .definitions import (
    ERROR_TITLE, get_verified_role_id, get_venus_channel_id,
    set_verified_role, set_venus_channel
)


class ConfigRoleSelect(discord.ui.RoleSelect):
    def __init__(self, guild):
        super().__init__(
            placeholder="Rôle",
            min_values=1,
            max_values=1,
        )
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        set_verified_role(interaction.guild.id, role)
        await interaction.response.edit_message(
            embed=build_config_embed(interaction.guild),
            view=ConfigRoleView(interaction.guild.id),
        )


class ConfigChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Salon",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        set_venus_channel(interaction.guild.id, channel)
        await interaction.response.edit_message(
            embed=build_config_embed(interaction.guild),
            view=ConfigRoleView(interaction.guild.id),
        )


class ConfigRoleView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.add_item(ConfigRoleSelect(None))
        self.add_item(ConfigChannelSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True

        embed = discord.Embed(
            title=ERROR_TITLE,
            description="Tu n'as pas la permission",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False


def build_config_embed(guild: discord.Guild) -> discord.Embed:
    role_id = get_verified_role_id(guild.id)
    channel_id = get_venus_channel_id(guild.id)
    role = guild.get_role(role_id)
    channel = guild.get_channel(channel_id)

    lines = []
    lines.append(f"Rôle de vérification : {role.mention if role else '*Non configuré*'}")
    lines.append(f"Salon de vérification : {channel.mention if channel else '*Tous les salons*'}")

    return discord.Embed(
        title="Configuration",
        description="\n".join(lines),
        color=discord.Color.blurple() if role else discord.Color.orange(),
    )


class ConfigurerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="configurer", description="[ADMIN] Configure le rôle et le salon de vérification")
    @discord.app_commands.default_permissions(administrator=True)
    async def config_cmd(self, interaction: discord.Interaction):
        embed = build_config_embed(interaction.guild)
        view = ConfigRoleView(interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ConfigurerCog(bot))

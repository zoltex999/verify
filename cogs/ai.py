import discord
from discord.ext import commands
from .definitions import (
    GEMINI_OFFTOPIC_MESSAGE, is_message_about_bot_context, ask_gemini_about_bot,
    build_error_embed
)


class IACog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="ia", description="Pose une question sur le bot et son environnement")
    @discord.app_commands.describe(prompt="prompt")
    async def ia_cmd(self, interaction: discord.Interaction, prompt: str):
        if not is_message_about_bot_context(prompt):
            await interaction.response.send_message(
                embed=build_error_embed(GEMINI_OFFTOPIC_MESSAGE),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        answer = await ask_gemini_about_bot(prompt, self.bot)
        is_offtopic = answer == GEMINI_OFFTOPIC_MESSAGE
        await interaction.followup.send(answer[:1900], ephemeral=is_offtopic)


async def setup(bot):
    await bot.add_cog(IACog(bot))

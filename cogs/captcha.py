import discord
import time
from .definitions import (
    ERROR_TITLE, pending_captchas, failed_captcha_attempts, 
    failed_captcha_streaks, cooldown_refresh_tasks, CAPTCHA_COLORS,
    generate_captcha_text, generate_captcha_image, send_captcha_dm,
    get_verified_role_id, notify_owner
)


class CaptchaModal(discord.ui.Modal, title="Captcha"):
    def __init__(self, bot, user_id: int, guild_id: int, button_message: discord.Message, started_at: float):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.button_message = button_message
        self.started_at = started_at
        self.reponse = discord.ui.TextInput(
            label="Code",
            required=True,
            max_length=8,
        )
        self.color_select = discord.ui.Select(
            placeholder="Couleur",
            options=[
                discord.SelectOption(label=name, value=name)
                for name, _ in CAPTCHA_COLORS
            ],
        )
        self.add_item(self.reponse)
        self.add_item(discord.ui.Label(text="Couleur", component=self.color_select))

    async def on_submit(self, interaction: discord.Interaction):
        now = int(time.time())
        retry_at = failed_captcha_attempts.get(self.user_id, 0)
        if now < retry_at:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"Tu dois attendre encore <t:{retry_at}:R> avant une nouvelle tentative",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        elapsed = time.monotonic() - self.started_at
        if elapsed < 3:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description="Tu dois attendre au moins 3 secondes avant de valider",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        captcha_data = pending_captchas.get(self.user_id, {})
        expected_code = captcha_data.get("code", "").upper()
        expected_color = captcha_data.get("color", "").upper()
        user_code = self.reponse.value.strip().upper()
        user_color = self.color_select.values[0].upper() if self.color_select.values else ""

        if user_code == expected_code and user_color == expected_color:
            pending_captchas.pop(self.user_id, None)
            failed_captcha_attempts.pop(self.user_id, None)
            failed_captcha_streaks.pop(self.user_id, None)
            refresh_task = cooldown_refresh_tasks.pop(self.user_id, None)
            if refresh_task:
                refresh_task.cancel()
            role_add_error: str | None = None
            guild = self.bot.get_guild(self.guild_id)
            if guild:
                member = guild.get_member(self.user_id)
                if member:
                    role_id = get_verified_role_id(self.guild_id)
                    role = guild.get_role(role_id)
                    if role:
                        try:
                            await member.add_roles(role, reason="Vérification réussie")
                        except discord.Forbidden:
                            role_add_error = (
                                "Je ne peux pas te donner le rôle de vérification"
                                "Le bot n'a pas la permission suffisante"
                            )
                            await notify_owner(
                                guild,
                                "Le bot ne peut pas attribuer le rôle de vérification"
                                "Place le rôle du bot au-dessus du rôle de vérification et vérifie la permission `Gérer les rôles`",
                            )
                        except discord.HTTPException:
                            role_add_error = "Une erreur Discord est survenue pendant l'attribution du rôle"
                    else:
                        role_add_error = "Le rôle de vérification configuré est introuvable"
                        await notify_owner(
                            guild,
                            "Un membre a réussi la vérification mais le rôle configuré est introuvable"
                            "Reconfigure-le avec </configurer:1494600343512678564>",
                        )
                else:
                    role_add_error = "Tu n'es plus présent sur le serveur"
            else:
                role_add_error = "Serveur introuvable"

            disabled_view = discord.ui.View()
            disabled_button = discord.ui.Button(
                label="Vérifié", style=discord.ButtonStyle.secondary, disabled=True
            )
            disabled_view.add_item(disabled_button)
            try:
                    await self.button_message.edit(view=disabled_view)
            except Exception:
                pass

            if role_add_error:
                embed = discord.Embed(
                    title=ERROR_TITLE,
                    description=role_add_error,
                    color=discord.Color.red(),
                )
            else:
                embed = discord.Embed(
                    title="<:verify:1494667945505456159> Vérifié",
                    description="Tu as maintenant accès au serveur !",
                    color=discord.Color.green(),
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            streak = failed_captcha_streaks.get(self.user_id, 0) + 1
            failed_captcha_streaks[self.user_id] = streak
            retry_delay = 15 * streak
            retry_at = int(time.time()) + retry_delay
            failed_captcha_attempts[self.user_id] = retry_at
            pending_captchas.pop(self.user_id, None)

            disabled_view = discord.ui.View(timeout=None)
            disabled_verify = discord.ui.Button(
                label="Entrer le code", style=discord.ButtonStyle.success, disabled=True
            )
            disabled_regen = discord.ui.Button(
                label="Régénérer", style=discord.ButtonStyle.secondary, disabled=True
            )
            disabled_view.add_item(disabled_verify)
            disabled_view.add_item(disabled_regen)
            try:
                await self.button_message.edit(view=disabled_view)
            except Exception:
                pass

            refresh_task = cooldown_refresh_tasks.pop(self.user_id, None)
            if refresh_task:
                refresh_task.cancel()

            async def recreate_verification_after_cooldown():
                try:
                    import asyncio
                    wait_seconds = max(0, retry_at - int(time.time()))
                    if wait_seconds:
                        await asyncio.sleep(wait_seconds)

                    failed_captcha_attempts.pop(self.user_id, None)
                    guild = self.bot.get_guild(self.guild_id)
                    if guild is None:
                        return

                    user = self.bot.get_user(self.user_id)
                    if user is None:
                        user = await self.bot.fetch_user(self.user_id)

                    await send_captcha_dm(user, guild, self.bot, clear_all=True)
                except Exception:
                    pass
                finally:
                    cooldown_refresh_tasks.pop(self.user_id, None)

            cooldown_refresh_tasks[self.user_id] = self.bot.loop.create_task(recreate_verification_after_cooldown())
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=(
                    f"Le code ou la couleur ne correspond pas\n"
                    f"Réessaie <t:{retry_at}:R>"
                ),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class CaptchaButton(discord.ui.View):
    def __init__(self, guild_id: int, captcha_code: str, captcha_color: str):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.captcha_code = captcha_code
        self.captcha_color = captcha_color

    @discord.ui.button(label="Entrer le code", style=discord.ButtonStyle.success)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        pending_captchas[interaction.user.id] = {
            "code": self.captcha_code,
            "color": self.captcha_color,
        }
        modal = CaptchaModal(
            interaction.client,
            interaction.user.id,
            self.guild_id,
            interaction.message,
            started_at=time.monotonic(),
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Régénérer", style=discord.ButtonStyle.secondary)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        now = int(time.time())
        retry_at = failed_captcha_attempts.get(interaction.user.id, 0)
        if now < retry_at:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"Tu dois attendre encore <t:{retry_at}:R> avant de régénérer",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        refresh_task = cooldown_refresh_tasks.pop(interaction.user.id, None)
        if refresh_task:
            refresh_task.cancel()

        pending_captchas.pop(interaction.user.id, None)

        guild = interaction.client.get_guild(self.guild_id)
        if guild is None:
            embed = discord.Embed(
                title=ERROR_TITLE,
                description="Le serveur est introuvable",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await send_captcha_dm(interaction.user, guild, interaction.client, clear_all=True)

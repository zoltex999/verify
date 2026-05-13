import discord
import os
import json
import io
import time
import sys
import re
import asyncio
import random
from captcha.image import ImageCaptcha
from google import genai


ERROR_TITLE = "<:venus_red:1494668360049492150> Erreur"
OWNER_USER_ID = 1022157841546625065
BOT_STARTED_AT = int(time.time())
SUPPORT_SERVER = "https://discord.gg/TCUTkQBxwP"
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_OFFTOPIC_MESSAGE = (
    "Je peux répondre uniquement aux questions liées au bot, "
    "à ses commandes et à son environnement Discord."
)

CONFIG_FILE = "config.json"

BOT_CONTEXT_KEYWORDS = {
    "bot",
    "discord",
    "serveur",
    "guild",
    "commande",
    "slash",
    "verifier",
    "verification",
    "captcha",
    "configurer",
    "role",
    "salon",
    "channel",
    "dm",
    "message prive",
    "reset",
    "premium",
    "relancer",
    "help",
    "permissions",
    "permission",
    "api",
    "token",
    "erreur",
    "bug",
    "latence",
    "hebergement",
    "logs",
    "uptime",
    "environnement",
    "config",
    "ia",
    "gemini",
    "createur",
    "developer",
    "auteur",
    "qui",
    "combien",
    "statistiques",
    "stats",
    "nombre",
    "utilisateurs",
}

CAPTCHA_COLORS = [
    ("Rouge", (255, 0, 0, 255)),
    ("Bleu", (0, 0, 255, 255)),
    ("Vert", (0, 128, 0, 255)),
    ("Orange", (255, 140, 0, 255)),
    ("Violet", (128, 0, 128, 255)),
    ("Jaune", (255, 215, 0, 255)),
    ("Rose", (255, 105, 180, 255)),
]

# Global state
pending_captchas: dict[int, dict] = {}
failed_captcha_attempts: dict[int, int] = {}
failed_captcha_streaks: dict[int, int] = {}
cooldown_refresh_tasks: dict[int, asyncio.Task] = {}

_gemini_client: genai.Client | None = None

# Config functions
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_verified_role_id(guild_id):
    config = load_config()
    return config.get(str(guild_id), {}).get("verified_role_id", 0)


def get_venus_channel_id(guild_id):
    config = load_config()
    return config.get(str(guild_id), {}).get("venus_channel_id", 0)


def set_venus_channel(guild_id: int, channel: discord.TextChannel):
    config = load_config()
    guild_key = str(guild_id)
    if guild_key not in config:
        config[guild_key] = {}
    config[guild_key]["venus_channel_id"] = channel.id
    save_config(config)


def set_verified_role(guild_id: int, role: discord.Role):
    config = load_config()
    guild_key = str(guild_id)
    if guild_key not in config:
        config[guild_key] = {}
    config[guild_key]["verified_role_id"] = role.id
    save_config(config)


# Embed builders
def build_error_embed(description: str) -> discord.Embed:
    return discord.Embed(
        title=ERROR_TITLE,
        description=description,
        color=discord.Color.red(),
    )


def build_success_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue(),
    )


# Utility functions
def is_owner_user(user_id: int) -> bool:
    return user_id == OWNER_USER_ID


def normalize_text(text: str) -> str:
    normalized = text.lower().strip()
    replacements = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "à": "a",
        "â": "a",
        "ä": "a",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "ö": "o",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
        "'": " ",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def is_message_about_bot_context(text: str) -> bool:
    normalized = normalize_text(text)
    if any(keyword in normalized for keyword in BOT_CONTEXT_KEYWORDS):
        return True

    allowed_commands = {"/verifier", "/configurer", "/reset", "/premium", "/bot", "/help", "/relancer", "/ia"}
    return any(command in normalized for command in allowed_commands)


def get_verified_role(guild: discord.Guild) -> discord.Role | None:
    role_id = get_verified_role_id(guild.id)
    if not role_id:
        return None
    return guild.get_role(role_id)


# Gemini
def get_gemini_client() -> genai.Client | None:
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


async def ask_gemini_about_bot(prompt: str, bot) -> str:
    client = get_gemini_client()
    if client is None:
        return (
            "La clé Gemini est introuvable. "
            "Ajoute GEMINI_API_KEY (ou GOOGLE_API_KEY) dans ton .env."
        )

    servers = len(bot.guilds)
    users = len(set(bot.get_all_members()))
    
    guarded_prompt = (
        "Je suis le bot Discord de verification humaine. "
        "Je dois repondre aux questions sur mon bot, mes commandes, ma configuration, "
        "ma moderation, mon environnement Discord et mon hebergement. "
        "Je suis hébérgé par ouiheberg. "
        "Je réponds uniquement a ce que l'utilisateur me demande, je n'ajoute pas de détails inutiles ou hors sujets. "
        f"Je suis present sur {servers} serveurs et {users} utilisateurs m'utilisent. "
        f"Mon createur est <@{OWNER_USER_ID}>. "
        f"Si la question est hors contexte, reponds exactement: {GEMINI_OFFTOPIC_MESSAGE}\n\n"
        f"Question utilisateur: {prompt}"
    )

    def _generate() -> str:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=guarded_prompt,
        )
        return (response.text or "").strip()

    try:
        answer = await asyncio.to_thread(_generate)
    except Exception:
        return "Impossible de contacter Verify pour le moment."

    if not answer:
        return "Verify n'a pas retourne de reponse exploitable."
    return answer


# Captcha
def generate_captcha_text(length=6):
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))


def generate_captcha_image(text: str, fg_color: tuple = None) -> io.BytesIO:
    image = ImageCaptcha(width=560, height=180, font_sizes=[120], fonts=None)
    im = image.generate_image(text, fg_color=fg_color)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    return buf


async def clear_dm(channel, only_bot: bool = True, bot_user=None):
    async for msg in channel.history(limit=100):
        if only_bot and msg.author != bot_user:
            continue
        try:
            await msg.delete()
        except Exception:
            pass


async def send_captcha_dm(user: discord.abc.User, guild: discord.Guild, bot, clear_all: bool = False):
    color_name, color_rgba = random.choice(CAPTCHA_COLORS)
    code = generate_captcha_text(length=6)
    image_buf = generate_captcha_image(code, fg_color=color_rgba)

    dm = await user.create_dm()
    await clear_dm(dm, only_bot=not clear_all, bot_user=bot.user)

    embed_dm = discord.Embed(
        title="Vérification",
        description="Clique sur le bouton ci-dessous pour te vérifier sur **{}**".format(guild.name),
        color=discord.Color.green(),
    )
    file = discord.File(fp=image_buf, filename="captcha.png")
    embed_dm.set_image(url="attachment://captcha.png")

    from .captcha import CaptchaButton
    view = CaptchaButton(guild_id=guild.id, captcha_code=code, captcha_color=color_name)
    await dm.send(embed=embed_dm, file=file, view=view)


async def notify_owner(guild: discord.Guild, problem: str):
    try:
        owner = guild.owner or await guild.fetch_member(guild.owner_id)
        embed = discord.Embed(
            title=ERROR_TITLE,
            description=(
                f"Un problème a été détecté sur **{guild.name}** :\n\n"
                f"{problem}\n\n"
                f"Si tu penses que ce n'est pas de ta faute, ouvre un ticket : {SUPPORT_SERVER}"
            ),
            color=discord.Color.red(),
        )
        await owner.send(embed=embed)
    except Exception:
        pass

import discord
import itertools
from discord.ext import commands, tasks
from .definitions import (
    ask_gemini_about_bot, is_message_about_bot_context, GEMINI_OFFTOPIC_MESSAGE
)


STATUS_LIST = [
    ".gg/2RpMGh4Thv",
    "Version Beta"
]


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._status_cycle = itertools.cycle(STATUS_LIST)
        self.rotate_status.start()

    def cog_unload(self):
        self.rotate_status.cancel()

    @tasks.loop(seconds=15)
    async def rotate_status(self):
        activity = discord.CustomActivity(name=next(self._status_cycle))
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    @rotate_status.before_loop
    async def before_rotate_status(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.bot.user}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or self.bot.user is None:
            return

        is_mentioned = self.bot.user in message.mentions
        is_reply = await self.is_reply_to_bot_message(message)
        if not (is_mentioned or is_reply):
            return

        cleaned_content = message.content
        cleaned_content = cleaned_content.replace(f"<@{self.bot.user.id}>", "")
        cleaned_content = cleaned_content.replace(f"<@!{self.bot.user.id}>", "")
        cleaned_content = cleaned_content.strip()

        if not cleaned_content:
            return

        if not is_message_about_bot_context(cleaned_content):
            await message.reply(GEMINI_OFFTOPIC_MESSAGE, mention_author=False)
            return

        async with message.channel.typing():
            answer = await ask_gemini_about_bot(cleaned_content, self.bot)

        if not answer:
            answer = "Je n'ai pas pu génerer de reponse."
        await message.reply(answer[:1900], mention_author=False)

    async def is_reply_to_bot_message(self, message: discord.Message) -> bool:
        if self.bot.user is None or message.reference is None or message.reference.message_id is None:
            return False

        resolved = message.reference.resolved
        if isinstance(resolved, discord.Message):
            return resolved.author.id == self.bot.user.id

        try:
            referenced = await message.channel.fetch_message(message.reference.message_id)
        except Exception:
            return False
        return referenced.author.id == self.bot.user.id


async def setup(bot):
    await bot.add_cog(EventsCog(bot))

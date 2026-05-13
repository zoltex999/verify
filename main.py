import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class VerifyBot(commands.Bot):
    async def setup_hook(self):
        guild_id = os.getenv("GUILD_ID", "").strip()
        if guild_id.isdigit():
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"{len(synced)} sync [ok]{guild_id}")
        else:
            synced = await self.tree.sync()
            print(f"{len(synced)} sync [ok] global")


bot = VerifyBot(command_prefix="/", intents=intents)


async def load_cogs():
    for filename in os.listdir("./cogs"):
        if (
            filename.endswith(".py")
            and not filename.startswith("_")
            and filename not in {"definitions.py", "captcha.py"}
        ):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"✅ Chargé: cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

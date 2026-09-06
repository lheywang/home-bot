# ----------------------------------------------------------------------------------
# brief : Launch the bot services
# author : l.heywang
# date : 06/09/2026
# ----------------------------------------------------------------------------------

# Imports
import asyncio
import os
import sys
import discord
import time
from discord.ext import commands

from network import networkEngine
from search import searchEngine


class HardwareBot(commands.Bot):

    def __init__(self, network: networkEngine, search_engine: searchEngine) -> None:

        # Express our intents
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

        # Inject the dependencies
        self.network: networkEngine = network
        self.search_engine: searchEngine = search_engine

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.search")
        await self.tree.sync()
        print("[INFO] Synchronized tree commands.")

    async def close(self) -> None:
        await super().close()
        await self.network.close()
        print("[INFO] Closed the network session.")


async def main() -> None:
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("[ERROR] Missing discord token variable.")
        sys.exit(1)

    index_url = "https://www.home-hardware.app/index.json"

    # Connect to the webite
    network = await networkEngine.create(url=index_url)

    # Initialize the network engine
    search_engine = searchEngine()

    await network.fetch()
    data, _ = network.get_data()
    search_engine.update(data)

    # Start the bot
    bot = HardwareBot(network=network, search_engine=search_engine)

    try:
        print("[INFO] Bot started !")
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.close()
        print("[INFO] Closed")


if __name__ == "__main__":
    asyncio.run(main())

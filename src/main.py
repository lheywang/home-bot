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

server = discord.Object(id=421053205409955841)


class HardwareBot(commands.Bot):

    def __init__(
        self,
        network: networkEngine,
        resources: networkEngine,
        links: networkEngine,
        errors: networkEngine,
        search_engine: searchEngine,
        resource_url: str,
        home_url: str,
        icon_url: str,
    ) -> None:

        # Express our intents
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

        # Inject the dependencies
        self.network: networkEngine = network
        self.search_engine: searchEngine = search_engine
        self.resources: networkEngine = resources
        self.links: networkEngine = links
        self.errors: networkEngine = errors
        self.resource_url = resource_url
        self.home = home_url
        self.icon = icon_url

    async def setup_hook(self) -> None:
        # Standard modules
        await self.load_extension("cogs.errors")
        await self.load_extension("cogs.search")
        await self.load_extension("cogs.image")
        await self.load_extension("cogs.links")
        print("[INFO] Loaded all extensions")

        # Slash commands sync
        await self.tree.sync()
        print("[INFO] Synchronized tree commands globally.")

        # Dev sync :
        self.tree.copy_global_to(guild=server)
        synced = await self.tree.sync(guild=server)
        print(
            f"[INFO] Synchronized {len(synced)} commands to the /home/hardware server. "
        )

        # Final print
        print("[INFO] Bot started ! Ready to interact.")

    async def close(self) -> None:
        await super().close()
        await self.network.close()
        print("[INFO] Closed the network session.")


async def main() -> None:
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("[ERROR] Missing discord token variable.")
        sys.exit(1)

    # Home URL
    home_url = "https://www.home-hardware.app/"

    # Base index URL :
    index_url = "https://www.home-hardware.app/index.json"
    icon_url = "https://www.home-hardware.app/icon.png"

    # Resources config :
    resource_url = "https://www.home-hardware.app/resources/"
    resource_list = "https://www.home-hardware.app/resources/resources.json"
    links_url = "https://www.home-hardware.app/resources/links.json"
    errors_url = "https://www.home-hardware.app/resources/errors.json"

    # Connect to the website
    network = await networkEngine.create(url=index_url)
    res = await networkEngine.create(url=resource_list)
    links = await networkEngine.create(url=links_url)
    errors = await networkEngine.create(url=errors_url)

    # Initialize the network engine
    search_engine = searchEngine()

    # Fetch the different resources
    await network.fetch()
    data, _ = network.get_data()
    search_engine.update(data)

    await res.fetch()
    await links.fetch()
    await errors.fetch()

    # Start the bot
    bot = HardwareBot(
        network=network,
        resources=res,
        links=links,
        errors=errors,
        search_engine=search_engine,
        resource_url=resource_url,
        home_url=home_url,
        icon_url=icon_url,
    )

    try:
        print("[INFO] Starting Bot ...")
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.close()
        print("[INFO] Closed")


if __name__ == "__main__":
    asyncio.run(main())

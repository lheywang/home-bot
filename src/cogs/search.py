# ----------------------------------------------------------------------------------
# brief : Define the bot search engine
# author : l.heywang
# date : 06/09/2026
# ----------------------------------------------------------------------------------


from datetime import datetime, timezone
from typing import Any, List
import discord
from discord import app_commands
from discord.ext import commands

from search import searchEngine
from network import networkEngine


def _confidence_bar(confidence: float, lengh: int = 10) -> str:
    filled = min(lengh, int(round((confidence / 100) * lengh)))
    bar = "█" * filled + "░" * (lengh - filled)
    return f"|{bar}| **{confidence:.1f}%**"


class SearchCog(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot,
        search_engine: searchEngine,
        network: networkEngine,
        home_url: str,
    ) -> None:
        self.bot: commands.Bot = bot
        self.search_engine: searchEngine = search_engine
        self.network: networkEngine = network
        self.home = home_url

    def _build_embed(
        self, query: str, confidence: float, articles: List[dict[str, Any]]
    ) -> discord.Embed:
        """Build the search result embed"""
        best = articles[0]
        slug = best.get("slug", "").lstrip("/")
        best_url = f"{self.home}/{slug}/"

        # Ensure the base URL is conform
        best_url = best_url.lower().replace("'", "")

        # Change the color based on the confidence we got
        if confidence >= 60.0:
            color = 0x2ECC71
        elif confidence >= 20.0:
            color = 0xE67E22
        else:
            color = 0xFC1C03

        # UNIX timestamp
        ts = best.get("date", 0.0)

        embed = discord.Embed(
            title=best.get("title", "Article sans titre"),
            url=best_url,
            color=color,
            timestamp=datetime.now(),
        )

        author = best.get("author", "Anonyme")
        avatar_name = author.lower().replace(" ", "_")
        embed.set_author(
            name=author,
            icon_url=f"{self.home}/avatars/{avatar_name}.png",
        )

        # Add an image
        embed.set_thumbnail(url=f"{self.home}/public/favicon.svg")

        # Add the confidence bar
        embed.add_field(
            name="Pertinence", value=_confidence_bar(confidence), inline=True
        )

        date_val = f"<t:{int(ts)}:d> (<t:{int(ts)}:R>)" if ts else "Inconnue"
        embed.add_field(name="Mise à jour", value=date_val, inline=True)

        # Adding others results
        if len(articles) > 1:
            connexes = []
            for item in articles[1:]:
                item_slug = item.get("slug", "").lstrip("/").lower()
                item_url = f"{self.home}/{item_slug}/"
                connexes.append(f"• [{item.get('title')}]({item_url})")

            embed.add_field(
                name="Articles connexes",
                value="\n".join(connexes),
                inline=False,
            )

        embed.set_footer(text=f"Recherche : « {query} »")
        return embed, best_url

    @app_commands.command(
        name="search",
        description="Recherche un guide ou tutoriel hardware sur le site",
    )
    @app_commands.describe(query="Mots-clés (ex: vrm, formatage ssd, mbr gpt)")
    async def search_command(
        self,
        interaction: discord.Interaction,
        query: str,
        size: app_commands.Range[int, 1, 10] = 3,
    ) -> None:

        # Fetch the the latest buffer (from RAM) and update the search engine if the database did change
        data, updated = self.network.get_data()
        if updated:
            self.search_engine.update(data)

        # Query
        confidence, results = self.search_engine.search(query, num=size)

        # Ensure we never respond garbage
        if not results or confidence < 5.0:
            await interaction.response.send_message(
                f"Aucun article pertinent trouvé pour « **{query}** ».\n"
                "Essaie avec des termes techniques plus précis (ex: `csm`, `pilote`, `carte mere`).",
                ephemeral=True,
            )
            return

        embed, best_url = self._build_embed(query, confidence, results)

        # Add an home page link
        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label="Meilleur résultat",
                url=best_url,
                style=discord.ButtonStyle.link,
                emoji="🥳",
            )
        )

        view.add_item(
            discord.ui.Button(
                label="Site web",
                url=self.home,
                style=discord.ButtonStyle.url,
                emoji="💻",
            )
        )

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:

    search_engine = getattr(bot, "search_engine", None)
    if search_engine is None:
        raise RuntimeError("Unable to load SearchCog without bot.search_engine loaded.")

    network = getattr(bot, "network", None)
    if network is None:
        raise RuntimeError("Unable to load SearchCog without bot.network loaded.")

    home = getattr(bot, "home", None)
    if home is None:
        raise RuntimeError("Unable to load SearchCog without bot.home loaded.")

    await bot.add_cog(SearchCog(bot, search_engine, network, home))

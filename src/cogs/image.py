# ----------------------------------------------------------------------------------
# brief : Define the bot image system
# author : l.heywang
# date : 08/09/2026
# ----------------------------------------------------------------------------------

# Imports
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from network import networkEngine


def _format_label(filename: str) -> str:
    """
    Make the filename cleaner on appearance
    """
    stem = filename.rsplit(".", 1)[0]
    tokens = stem.split("_")
    category = tokens[0].upper()
    label = " ".join(tokens[1:]).capitalize()
    return f"[{category}] {label}"


def _create_view(url: str, site: Optional[str] = None) -> discord.ui.View:
    """
    Build buttons to get an access to the image in a bigger format.
    """
    view = discord.ui.View()

    view.add_item(
        discord.ui.Button(
            label="Plein écran (HD)",
            url=url,
            style=discord.ButtonStyle.link,
            emoji="🔍",
        )
    )

    if site:
        view.add_item(
            discord.ui.Button(
                label="Site web", url=site, style=discord.ButtonStyle.url, emoji="💻"
            )
        )

    return view


class ImageCog(commands.Cog):
    """
    Base class for the image search engine
    """

    def __init__(
        self,
        bot: commands.Bot,
        resource_manager: networkEngine,
        base_url: str,
        home_url: str,
        icon_url: str,
    ) -> None:
        self.bot = bot
        self.res = resource_manager
        self.url = base_url
        self.home = home_url
        self.icon = icon_url
        print("[INFO] Loaded ImageCog")
        return

    @app_commands.command(
        name="image",
        description="Search for the specified resource and link it to you !",
    )
    @app_commands.describe(
        schema="Keyword or filepath", target="Member to ping for with the answer"
    )
    async def image(
        self,
        interaction: discord.Interaction,
        schema: str,
        target: Optional[discord.Member] = None,
    ) -> None:
        """
        Slash command to search for an image and link it to you !
        """

        # Ensure the file is available
        valids, _ = self.res.get_data()
        if schema not in valids:
            await interaction.response.send_message(
                "Could not find requested resource. Try another option.", ephemeral=True
            )
            return

        # Now, build the embed
        url = f"{self.url}{schema}"
        title = _format_label(schema)

        embed = discord.Embed(title=title, color=0x3498DB)
        embed.set_image(url=url)
        embed.set_footer(
            text=f"Interaction demandée par {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        # Build the content
        content: Optional[str] = f"Ressource pour {target.mention}" if target else None

        # Add the view
        view = _create_view(url, self.home)

        print(f"[LOG] Image query returned {url}")

        await interaction.response.send_message(content=content, embed=embed, view=view)

    @image.autocomplete("schema")
    async def image_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """
        Filter the available schematics !
        """
        query_tokens = current.strip().lower().split()
        available, _ = self.res.get_data()

        choices = []
        for filename in available:

            search_space = filename.replace("_", " ").lower()

            if all(token in search_space for token in query_tokens):
                display_name = _format_label(filename)
                choices.append(
                    app_commands.Choice(
                        name=display_name[:100],
                        value=filename,
                    )
                )

            if len(choices) >= 25:
                break

        return choices


async def setup(bot: commands.Bot) -> None:
    """
    Configuration of the image search engine.
    """
    resource_engine = getattr(bot, "resources", None)
    if resource_engine is None:
        raise RuntimeError(
            "Unable to load ImageCog without bot.resource_engine loaded."
        )

    url = getattr(bot, "resource_url", None)
    if url is None:
        raise RuntimeError("Unable to load ImageCog without bot.resource_url loaded.")

    home = getattr(bot, "home", None)
    if home is None:
        raise RuntimeError("Unable to load ImageCog without bot.home loaded.")

    icon_url = getattr(bot, "icon", None)
    if icon_url is None:
        raise RuntimeError("Unable to load ImageCog without bot.errors_engine loaded.")

    await bot.add_cog(ImageCog(bot, resource_engine, url, home, icon_url))

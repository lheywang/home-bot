# ----------------------------------------------------------------------------------
# brief : Define the bot linking system
# author : l.heywang
# date : 08/09/2026
# ----------------------------------------------------------------------------------

# Imports
from typing import Optional
from urllib.parse import urlparse

import discord
from discord import app_commands
from discord.ext import commands

from network import networkEngine


def _format_label(name: str) -> str:
    """
    Make the filename cleaner on appearance
    """
    tokens = name.split("_")
    category = tokens[0].upper()
    label = " ".join(tokens[1:]).capitalize()
    return f"[{category}] {label}"


def _create_view(url: str) -> discord.ui.View:
    """
    Build buttons to get an access to the image in a bigger format.
    """
    view = discord.ui.View()

    view.add_item(
        discord.ui.Button(
            label="Ouvrir le lien",
            url=url,
            style=discord.ButtonStyle.link,
            emoji="📖",
        )
    )

    return view


class LinksCog(commands.Cog):
    """
    Base class for the image search engine
    """

    def __init__(
        self,
        bot: commands.Bot,
        links: networkEngine,
        icon_url: str,
    ) -> None:
        self.bot = bot
        self.links = links
        self.icon = icon_url
        print("[INFO] Loaded LinksCog")
        return

    @app_commands.command(
        name="link",
        description="Search for the specified resource and provide a links !",
    )
    @app_commands.describe(
        name="Name of the link", target="Member to ping for with the answer"
    )
    async def link(
        self,
        interaction: discord.Interaction,
        name: str,
        target: Optional[discord.Member] = None,
    ) -> None:
        """
        Slash command to search for a link and send it to you !
        """

        # Ensure the file is available
        data, _ = self.links.get_data()

        link_url = data.get(name, None)
        if link_url == None:
            await interaction.response.send_message(
                "Could not find requested resource. Try another option.", ephemeral=True
            )
            return

        # Now, build the embed
        title = _format_label(name)
        embed = discord.Embed(title=title, color=0x3498DB)
        embed.set_thumbnail(url=self.icon)

        # Add the domain name
        domain = urlparse(link_url).netloc
        embed.add_field(name="Source :", value=f"`{domain}`", inline=True)

        # Set the footer
        embed.set_footer(
            text=f"Interaction demandée par {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        # Build the content
        content: Optional[str] = f"Ressource pour {target.mention}" if target else None

        # Add the view
        view = _create_view(link_url)

        print(f"[LOG] Image query returned {link_url}")

        await interaction.response.send_message(content=content, embed=embed, view=view)

    @link.autocomplete("name")
    async def link_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """
        Filter the available schematics !
        """
        query = current.strip().lower()
        links_dict, _ = self.links.get_data()

        choices = []
        for title, data in links_dict.items():

            if query in title.lower():
                choices.append(
                    app_commands.Choice(
                        name=_format_label(title)[:100],
                        value=title,
                    )
                )

            if len(choices) >= 25:
                break

        return choices


async def setup(bot: commands.Bot) -> None:
    """
    Configuration of the links search engine.
    """
    links_engine = getattr(bot, "links", None)
    if links_engine is None:
        raise RuntimeError("Unable to load LinksCog without bot.links_engine loaded.")

    icon_url = getattr(bot, "icon", None)
    if icon_url is None:
        raise RuntimeError("Unable to load LinksCog without bot.errors_engine loaded.")

    await bot.add_cog(LinksCog(bot, links_engine, icon_url))

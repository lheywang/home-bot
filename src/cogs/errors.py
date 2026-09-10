# ----------------------------------------------------------------------------------
# brief : Define the bot image system
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


def _create_view(url: str) -> discord.ui.View:
    """
    Build buttons to get an access to the image in a bigger format.
    """

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="Ouvrir la solution",
            url=url,
            style=discord.ButtonStyle.link,
            emoji="📖",
        )
    )

    return view


class ErrorsCog(commands.Cog):
    """
    Base class for the image search engine
    """

    def __init__(
        self,
        bot: commands.Bot,
        errors_manager: networkEngine,
        icon_url: str,
    ) -> None:
        self.bot = bot
        self.errors = errors_manager
        self.icon = icon_url
        print("[INFO] Loaded ErrorsCog")
        return

    @app_commands.command(
        name="error",
        description="Search for the specified errors and link info to you !",
    )
    @app_commands.describe(
        code="Integer or hexadecimal code",
        target="Member to ping for with the answer",
    )
    async def error(
        self,
        interaction: discord.Interaction,
        code: str,
        target: Optional[discord.Member] = None,
    ) -> None:
        """
        Slash command to search for an error code and link informations to you !
        """

        # Ensure the file is available
        codes, _ = self.errors.get_data()

        # Fetch the error
        error_info = codes.get(code, None)
        if error_info == None:
            await interaction.response.send_message(
                "Could not find requested error code. Try another option.",
                ephemeral=True,
            )
            return

        # Now, build the embed
        title = error_info.get("name", "UNKNOWN")
        embed = discord.Embed(title=title, color=0x3498DB)
        embed.set_thumbnail(url=self.icon)

        # Fetch the URL
        error_url = error_info.get("url", "[UNKNOWN]")

        # Add the fields
        error_cause = error_info.get("cause", None)
        if error_cause != None:
            embed.add_field(name="Causes :", value=error_cause, inline=True)

        error_checks = error_info.get("checks", None)
        if error_checks != None:
            embed.add_field(name="Vérifie : ", value=error_checks, inline=True)

        embed.set_footer(
            text=f"Interaction demandée par {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        # Add an URL source
        if error_url != "":
            domain = urlparse(error_url).netloc
            embed.add_field(name="Source :", value=f"`{domain}`", inline=True)

        # Build the content
        content: Optional[str] = f"Ressource pour {target.mention}" if target else None

        # Logger

        print(f"[LOG] Error query {code} returned {error_url}")

        # Send the message with the optional view
        if error_url != "":
            view = _create_view(url=error_url)
            await interaction.response.send_message(
                content=content, embed=embed, view=view
            )
        else:
            await interaction.response.send_message(content=content, embed=embed)

    @error.autocomplete("code")
    async def error_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """
        Filter the available schematics !
        """
        query = current.strip().lower()
        query_clean = query.removeprefix("0x")

        data_codes, _ = self.errors.get_data()

        choices = []
        for int_code, data in data_codes.items():

            # Clean up the codes
            name = data.get("name", "").lower()

            # Build the codes as different formats :
            code = int(int_code, 10)
            dec_str = str(code)
            hex_str = f"{code:x}".lower()
            hex_full = f"0x{code:x}".lower()

            # Check for different match types
            match_name = query in name
            match_dec = query in dec_str
            match_hex = (query_clean in hex_str) or (query in hex_full)

            # Append if possible
            if match_name or match_dec or match_hex:
                label = f"{name.upper()} (0x{code:08X} / {code})"[:100]
                choices.append(
                    app_commands.Choice(
                        name=label,
                        value=int_code,
                    )
                )

            if len(choices) >= 25:
                break

        return choices


async def setup(bot: commands.Bot) -> None:
    """
    Configuration of the errors search engine.
    """
    errors_engine = getattr(bot, "errors", None)
    if errors_engine is None:
        raise RuntimeError("Unable to load ErrorsCog without bot.errors_engine loaded.")

    icon_url = getattr(bot, "icon", None)
    if icon_url is None:
        raise RuntimeError("Unable to load ErrorsCog without bot.errors_engine loaded.")

    await bot.add_cog(ErrorsCog(bot, errors_engine, icon_url))

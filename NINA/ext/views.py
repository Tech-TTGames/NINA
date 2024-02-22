"""Generic discord.py views for Project: NINA.

Those are various buttons and select menus used throughout the bot.
Note that these are not cogs, but rather discord.py views.

Typical usage example:
    ```py
    from NINA.ext import views

    @bot.command()
    async def example(ctx):
        await ctx.send("Example", view=views.ExampleView())
        ...
    ```
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames

import discord


class Confirm(discord.ui.View):
    """A confirmation button set.

    Allows the user to confirm or cancel an action.

    Attributes:
        value: Whether the user confirmed or not.
            `None` if the user didn't confirm or cancel.
            `bool` if the user confirmed or canceled.
    """

    value: bool | None

    def __init__(self, user: discord.User | discord.Member):
        """Initialises the view.

        We prep the button and set return value to None.
        """
        super().__init__()
        self.value = None
        self.user = user

    async def resolve(
        self,
        ctx: discord.Interaction,
        mgs: discord.Message,
        embed: discord.Embed,
        description: str | None,
        footer: str | None,
    ) -> bool:
        """Resolves the view.

        Basically waits for the user to confirm or cancel, then returns the value and edits the message.

        Args:
            ctx: The interaction that triggered the view.
            mgs: The message to edit.
            embed: The embed being edited.
            description: The description to set, if we succeed, if None, we set it to "Confirmed."
            footer: The footer to set, if confirmed, if None, no footer is set.

        Returns:
            Whether the user confirmed or not.
            Timeout is considered a cancel.
        """
        await self.wait()
        if self.value is None:
            embed.description = "Confirmation timed out."
            await ctx.followup.edit_message(mgs.id, embed=embed, view=None)
            return False
        if not self.value:
            embed.description = "Cancelled."
            embed.colour = discord.Color.orange()
            await ctx.followup.edit_message(mgs.id, embed=embed, view=None)
            return False
        embed.description = description or "Confirmed."
        embed.colour = discord.Color.green()
        embed.set_footer(text=footer)
        await ctx.followup.edit_message(mgs.id, embed=embed, view=None)
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """The 'Confirm' button was pressed.

        We set the return value to True, disable the button and stop the view.

        Args:
            interaction: The interaction that triggered the button.
            button: The button that was pressed.
        """
        if interaction.user != self.user:
            await interaction.response.send_message("You can't do that.", ephemeral=True)
            return
        await interaction.response.send_message("Confirmed", ephemeral=True)
        self.value = True
        button.disabled = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """The 'Cancel' button was pressed.

        We set the return value to False, disable the button and stop the view.

        Args:
            interaction: The interaction that triggered the button.
            button: The button that was pressed.
        """
        if interaction.user != self.user:
            await interaction.response.send_message("You can't do that.", ephemeral=True)
            return
        await interaction.response.send_message("Cancelled", ephemeral=True)
        self.value = False
        button.disabled = True
        self.stop()

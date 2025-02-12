from enum import Enum, auto
from message_util import next_message
import discord

class ImpersonationType(Enum):
    TECH_SUPPORT = auto()
    GOVERNMENT = auto()
    PROFESSIONAL = auto()
    SOMEONE_I_KNOW = auto()
    OTHER = auto()
    NEVERMIND = auto()
    CANCEL = auto()
    DEFAULT = auto()

# Here we give user different button options to identify the abuse type
class Impersonation(discord.ui.View):

    impersonation_type: ImpersonationType = ImpersonationType.CANCEL
    impersontator_info: str = None

    async def disable_all_items(self):
        for item in self.children:
            item.disabled=True
        await self.message.edit(view=self)

    async def on_timeout(self) -> None:
        await self.message.channel.send("Timed out.")
        await self.disable_all_items()

    async def get_additional_info(self):
        msg = await next_message()
        if msg == None:
            self.impersonation_type = ImpersonationType.CANCEL
        else:
            self.other_info = msg.content

    @discord.ui.button(label="TechSupport", style=discord.ButtonStyle.blurple)
    async def tech_option(self, interaction, button):
        await interaction.response.send_message("Thank you for letting us know. Note that no tech support firm or IT departments will need to ask you for your password or any authentication information.")
        await interaction.followup.send("Please provide the name of the company they were claiming to be from.")
        self.impersonation_type = ImpersonationType.TECH_SUPPORT
        await self.disable_all_items()
        await self.get_additional_info()
        self.stop()

    @discord.ui.button(label="Government / LE", style=discord.ButtonStyle.blurple)
    async def gov_option(self, interaction, button):
        await interaction.response.send_message("Please provide the name of the agency they claim to represent")
        self.impersonation_type = ImpersonationType.GOVERNMENT
        await self.disable_all_items()
        await self.get_additional_info()
        self.stop()

    @discord.ui.button(label="Professional", style=discord.ButtonStyle.blurple)
    async def professional_option(self, interaction, button):
        await interaction.response.send_message("Please provide the name of the company they claim to represent")
        self.impersonation_type = ImpersonationType.PROFESSIONAL
        await self.disable_all_items()
        await self.get_additional_info()
        self.stop()

    @discord.ui.button(label="Someone I Know", style=discord.ButtonStyle.blurple)
    async def someone_option(self, interaction: discord.Interaction, button):
        await interaction.response.send_message("Thank you for letting us know. If you're unsure if this user is actually someone you know, we recommend using another channel to confirm their claims.")
        await interaction.followup.send("Please describe in brief who you think this user is impersonating.")
        self.impersonation_type = ImpersonationType.SOMEONE_I_KNOW
        await self.disable_all_items()
        await self.get_additional_info()
        self.stop()

    @discord.ui.button(label="Other", style=discord.ButtonStyle.blurple)
    async def other_option(self, interaction, button):
        await interaction.response.send_message("Please describe in brief who you think this user is impersonating.")
        self.impersonation_type = ImpersonationType.OTHER
        await self.disable_all_items()
        await self.get_additional_info()
        self.stop()

    @discord.ui.button(label="Not applicable", style=discord.ButtonStyle.blurple)
    async def none_option(self, interaction, button):
        await interaction.response.send_message("Thank you, we will review this interraction. Please reply to this message to continue.")
        self.impersonation_type = ImpersonationType.NEVERMIND
        await self.disable_all_items()
        # await self.get_additional_info()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_option(self, interaction, button):
        await interaction.response.send_message("Leaving reporting flow")
        self.impersonation_type = ImpersonationType.CANCEL
        await self.disable_all_items()
        self.stop()
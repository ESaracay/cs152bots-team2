from enum import Enum, auto
import discord

class ReportType(Enum):
    OTHER = auto()
    SCAM = auto()
    SPAM = auto()
    CANCEL = auto()

# Here we give user different button options to identify the abuse type
class ReportReason(discord.ui.View):

    report_type: ReportType = ReportType.CANCEL

    async def disable_all_items(self):
        for item in self.children:
            item.disabled=True
        await self.message.edit(view=self)

    async def on_timeout(self) -> None:
        await self.message.channel.send("Timed out.")
        await self.disable_all_items()

    @discord.ui.button(label="Other", style=discord.ButtonStyle.blurple)
    async def other_option(self, interaction, button):
        await interaction.response.send_message("Taking you to the reporting flow for option other")
        self.report_type = ReportType.OTHER
        await self.disable_all_items()
        self.stop()

    @discord.ui.button(label="Possible Scam", style=discord.ButtonStyle.blurple)
    async def scam_option(self, interaction, button):
        await interaction.response.send_message("Taking you to the reporting flow for Scam")
        self.report_type = ReportType.SCAM
        await self.disable_all_items()
        self.stop()

    @discord.ui.button(label="Spam", style=discord.ButtonStyle.blurple)
    async def spam_option(self, interaction, button):
        await interaction.response.send_message("Taking you to the reporting flow for spam")
        self.report_type = ReportType.SPAM
        await self.disable_all_items()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_option(self, interaction, button):
        await interaction.response.send_message("Leaving reporting flow")
        self.report_type = ReportType.CANCEL
        await self.disable_all_items()
        self.stop()
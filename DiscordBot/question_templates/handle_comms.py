from enum import Enum, auto
import discord

class GFState(Enum):
    GOOD = auto()
    BAD = auto()

class WhoAreYouEnum(Enum):
    TECH_SUPPORT = auto()
    GOVT = auto()
    INDIV = auto()

class YesOrNo(Enum):
    YES = auto()
    NO = auto()

# Here we give user different button options to identify the abuse type
class GoodFaith(discord.ui.View):

    report_type: GFState = None

    async def disable_all_items(self):
        for item in self.children:
            item.disabled=True
        await self.message.edit(view=self)

    async def on_timeout(self) -> None:
        await self.message.channel.send("Timedout")
        await self.disable_all_items()

    @discord.ui.button(label="Good Faith", style=discord.ButtonStyle.blurple)
    async def other_option(self, interaction, button):
        await interaction.response.send_message("Taking you to the reporting flow for good faith report")
        self.report_type = GFState.GOOD
        await self.disable_all_items()
        self.stop()

    @discord.ui.button(label="Bad Faith", style=discord.ButtonStyle.blurple)
    async def spam_option(self, interaction, button):
        await interaction.response.send_message("Taking you to the reporting flow for bad faith report")
        self.report_type = GFState.BAD
        await self.disable_all_items()
        self.stop()

class WhoAreYou(discord.ui.View):
    report_type: WhoAreYouEnum = None

    async def disable_all_items(self):
        for item in self.children:
            item.disabled=True
        await self.message.edit(view=self)

    async def on_timeout(self) -> None:
        await self.message.channel.send("Timedout")
        await self.disable_all_items()

    @discord.ui.button(label="Tech Support", style=discord.ButtonStyle.blurple)
    async def other_option(self, interaction, button):
        await interaction.response.send_message("Ok.  They are claiming to be tech support. Did the user lose something?")
        await self.disable_all_items()
        self.stop()

    @discord.ui.button(label="Government", style=discord.ButtonStyle.blurple)
    async def random(self, interaction, button):
        await interaction.response.send_message("Ok. They are claiming to be the government. Did the user lose something?")
 
        await self.disable_all_items()
        self.stop()

    @discord.ui.button(label="Individual", style=discord.ButtonStyle.blurple)
    async def random_name(self, interaction, button):
        await interaction.response.send_message("Ok. They are claiming to be an individual. Did the user lose something?")

        await self.disable_all_items()
        self.stop()

class LoseSomething(discord.ui.View):
    report_type: YesOrNo = None

    async def disable_all_items(self):
        for item in self.children:
            item.disabled=True
        await self.message.edit(view=self)

    async def on_timeout(self) -> None:
        await self.message.channel.send("Timedout")
        await self.disable_all_items()


    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple)
    async def spam_option(self, interaction, button):
        await interaction.response.send_message("Ok. The user lost something. As a result, we will be banning the scammer")

        await self.disable_all_items()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.blurple)
    async def option_two(self, interaction, button):
        await interaction.response.send_message("Ok. The user didn't lose something. As a result, we will be issuing a warning to the scammer")

        await self.disable_all_items()
        self.stop()
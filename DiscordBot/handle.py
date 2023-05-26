from enum import Enum, auto
import discord
import re
from discord.ext.context import ctx
from question_templates.handle_comms import *

from message_util import next_message


class State(Enum):
    HANDLE_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    BAD_FAITH_CHECK = auto()
    GOOD_FLOW = auto()
    BAD_FLOW = auto()
    LOSS = auto()
    REPORT_COMPLETE = auto()
    REPORT_CANCELED = auto()

class Handle:
    START_KEYWORD = "handle"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        # TODO: Change back to report start
        self.state = State.HANDLE_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        
        if self.state == State.HANDLE_START:
            reply =  "Thank you for starting the handling process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Which message are you handling (include link)"
            await ctx.channel.send(''.join(reply))

            wait_for_message = True
            msg = await next_message()

            self.state = State.MESSAGE_IDENTIFIED
            print("new state")
        
        if self.state == State.MESSAGE_IDENTIFIED:
            await ctx.channel.send("Please choose whether this report is good faith or not.")
            # 30 second timeout wait
            print("INSIDE MESSAGE ID")
            report_reason = GoodFaith(timeout=30)

            message = await ctx.channel.send(view=report_reason)

            report_reason.message = message
            # Here we wait for the ReportReason class to wait for users button press
            await report_reason.wait()

            if report_reason.report_type == None:
                self.state = State.REPORT_CANCELED
            elif report_reason.report_type == GFState.GOOD:
                self.state = State.GOOD_FLOW
            elif report_reason.report_type == GFState.BAD:
                self.state = State.BAD_FLOW

        if self.state == State.BAD_FLOW:
            await ctx.channel.send("This user has sent one bad faith report recently.  Warning user.")

            self.state = State.REPORT_CANCELED
            
        if self.state == State.GOOD_FLOW:
            report_reason = WhoAreYou(timeout=30)

            message = await ctx.channel.send(view=report_reason)

            report_reason.message = message
            # Here we wait for the ReportReason class to wait for users button press
            await report_reason.wait()
            self.state = State.LOSS

        if self.state == State.LOSS:
            report_reason = LoseSomething(timeout=30)

            message = await ctx.channel.send(view=report_reason)

            report_reason.message = message
            # Here we wait for the ReportReason class to wait for users button press
            await report_reason.wait()
            self.state = State.REPORT_COMPLETE


        # TODO: Return our completed report class
        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE or self.state == State.REPORT_CANCELED
    
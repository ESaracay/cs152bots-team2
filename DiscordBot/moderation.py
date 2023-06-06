
from enum import Enum, auto
import discord
import re
from discord.ext.context import ctx
from message_util import next_message
from mongo_client import insert_record, find_bad_faith_reports
from report import ModerationRequest 
from question_templates.checking_scam import CheckingScam, ScamRequestType
from question_templates.reliable_report import ReportIsReliable, ReportReliability
from question_templates.impersonation import Impersonation, ImpersonationType

from datetime import datetime
import json
import logging
import uuid


logger = logging.getLogger("Moderation-Flow")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='moderation.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

MOD_CHANNEL = "group-2-mod"

class State(Enum):
   START = auto() 
   UNKNOWN_FAITH = auto()
   GOOD_FAITH = auto()
   BAD_FAITH = auto()
   CREATE_REPORT = auto()
   TIMED_OUT = auto()
   CANCELLED = auto ()
   COMPLETE = auto()
   ASSESS_SCORE = auto() # end state of report
   PUNITIVE_ACTION = auto() # if bad actor stole money or PII from user, follow this path to ban
                            # and offer followup to user - aka "Scam score 4"

class ReportType(Enum):
    USER_GENERATED = auto()
    AUTOMATED = auto()

class Moderation_Flow:
    def __init__(self, message: discord.Message, mod_channel, automated=False, scam_score=0, reporter:discord.Member = None, guild:discord.Guild = None):
        if automated:
            self.state = State.GOOD_FAITH
            self.report_type = ReportType.AUTOMATED
            self.scam_score = 0
            self.automated = True
        else:
            self.state = State.UNKNOWN_FAITH
            self.report_type = ReportType.USER_GENERATED
            self.scam_score = scam_score
            self.automated = False
        self.mod_channel = mod_channel
        self.message = message
        self.author = message.author
        # record entity being impersonated
        self.impersonation_type = ImpersonationType.DEFAULT
        self.impersonated = ""
        self.scam_type = ""
        self.incident_id = str(uuid.uuid4())
        self.reporter = reporter
        # self.reporter_id = reporter_id
        self.guild = guild
    
    def dump_report_state(self):
        persistent_dump = {
                "incident_id": self.incident_id,
                "incident_author": self.author.name,
                "incident_author_display_name": self.author.display_name,
                "incident_author_id": str(self.author.id),
                "incident_timestamp": str(self.message.created_at),
                "incident_reporter_id":  0 if self.automated else str(self.reporter.id),
                "message_text": self.message.content,
                "incident_scam_score": self.scam_score,
                "impersonated_party": self.impersonated,
                # "impersonation_type": self.impersonation_type
            }
        if self.state == State.BAD_FAITH:
            persistent_dump["bad_faith_report"] = True
        else:
            persistent_dump["bad_faith_report"] = False
        return persistent_dump

    def insert_moderation_report(self):
        if self.state != State.COMPLETE:
            return
        
        persistent_dump = self.dump_report_state()
        jsonified = json.dumps(persistent_dump)

        insert_record("moderation_reports", persistent_dump)
        logger.debug(jsonified)
        print("Logged report:", jsonified)
        print("Done!")

    def insert_bad_faith_report(self):
        if self.state != State.BAD_FAITH:
            return
        
        persistent_dump = self.dump_report_state()
        jsonified = json.dumps(persistent_dump)

        insert_record("bad_faith_reports", persistent_dump)
        logger.debug(jsonified)
        print("Logged bad faith report:", jsonified)

    def lookup_bad_faith_reports(self):
        # look up bad faith reports collection, return count matching this user ID
        num_bad_reports = find_bad_faith_reports(self.reporter.id)
        return num_bad_reports

    
    async def handle_moderation_report(self):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        await self.send_update_message(f'''Thank you for submitting your report. Our moderation team will begin reviewing this shortly.
                                       For future reference, your report ID is: {self.incident_id}.
                                       Our team will update you on the status of this report as soon as we can.''')

        if self.state == State.UNKNOWN_FAITH:
            await self.mod_channel.send("Did the user accurately follow the user reporting flow?")

            report_is_reliable = ReportIsReliable(timeout=200)

            msg = await self.mod_channel.send(view=report_is_reliable)

            report_is_reliable.message = msg

            await report_is_reliable.wait()

            if report_is_reliable.report_reliability == ReportReliability.GOOD:
                if self.report_type == ReportType.AUTOMATED:
                    self.scam_score += 1
                self.state = State.GOOD_FAITH
            elif report_is_reliable.report_reliability == ReportReliability.BAD:
                self.state = State.BAD_FAITH
            else:
                self.state = State.TIMED_OUT
            
        if self.state == State.BAD_FAITH:
            await self.mod_channel.send("Checking the total number of bad faith reports submitted by this user")
            #TODO: Keep track of total number of bad faith reports based on message.author.id, so keep a database in a csv file or some datastruct like a map
            # for now, print username/id to console
            self.insert_bad_faith_report()
            if self.lookup_bad_faith_reports() > 1:
                await self.send_banning_message(1)
            return

        if self.state == State.GOOD_FAITH:
            await self.mod_channel.send("Who does the alleged scammer claim to be?")
            #TODO: Create a class to collect this information similar to impersonation.py then save to database
            impersonator = Impersonation(timeout=45) 

            msg = await self.mod_channel.send(view=impersonator)

            impersonator.message = msg
            print("Got new message, current type is", impersonator.impersonation_type)

            impersonated_msg = await next_message(channel=MOD_CHANNEL)
            print("Got new message, current type is", impersonator.impersonation_type)

            if (impersonator.impersonation_type not in [
                ImpersonationType.CANCEL, ImpersonationType.DEFAULT, ImpersonationType.NEVERMIND
            ]):
                logger.debug(f"Report to: {impersonated_msg.content}")
                print("impersonation type recorded:", impersonator.impersonation_type)

            if impersonator.impersonation_type == ImpersonationType.CANCEL:
                await self.mod_channel.send("Report Cancelled")
                self.state = State.CANCELLED
            elif impersonator.impersonation_type == ImpersonationType.DEFAULT or impersonator.impersonation_type == ImpersonationType.NEVERMIND:
                print("in type DEFAULT or NEVERMIND")
                self.state = State.ASSESS_SCORE
            else:
                print("If we're here we should be in state transition")
                self.impersonation_type = impersonator.impersonation_type
                self.impersonated = impersonated_msg.content
                self.state = State.CREATE_REPORT
                if self.report_type == ReportType.AUTOMATED:
                    self.scam_score += 1
            print("Leaving GOOD_FAITH in state", self.state)

        if self.state == State.CREATE_REPORT:
            await self.mod_channel.send("Can you verify if this user gave any of the following to the scammer?")
            checking_scam = CheckingScam(timeout=30)

            msg = await self.mod_channel.send(view=checking_scam)

            checking_scam.message = msg
            res = await checking_scam.wait()

            self.scam_type = checking_scam.scam_type

            if checking_scam.scam_type == ScamRequestType.CANCEL:
                await self.mod_channel.send("Report Cancelled")
                self.state = State.CANCELLED
            # User didn't ask for anything
            elif checking_scam.scam_type != ScamRequestType.NONE:
                self.state = State.PUNITIVE_ACTION
            else:
                # self.report.increment_score()
                if self.report_type == ReportType.AUTOMATED:
                    self.scam_score += 1
                self.state = State.ASSESS_SCORE

        if self.state == State.ASSESS_SCORE:
            print("Scam score:", self.scam_score)
            if self.scam_score == 1:
                await self.send_warning_message()
                await self.send_update_message("Our team has issued a warning to the user you reported. Thank you again for bringing this to our attention.")
            elif self.scam_score == 2:
                await self.send_banning_message(1)
                await self.send_update_message("Our team has issued a temporary ban to the user you reported. Thank you again for bringing this to our attention.")
            elif self.scam_score == 3:
                await self.send_banning_message(7)
                await self.send_update_message("Our team has issued a one week ban to the user you reported. Thank you again for bringing this to our attention.")
            elif self.scam_score == 4:
                await self.send_permanent_banning_message()
                await self.send_update_message("Our team has permanently banned the user you reported. Thank you again for bringing this to our attention.")

            self.state = State.COMPLETE

        if self.state == State.PUNITIVE_ACTION:
            await self.send_permanent_banning_message()
            await self.send_update_message("Our team has permanently banned the user you reported. Thank you again for bringing this to our attention.")

            print("TODO: Offer reporting services to user")
            self.state = State.COMPLETE

        if self.state == State.COMPLETE:
            self.insert_moderation_report()

    async def send_update_message(self, message_content: str):
        # send message to self.reporter_id
        # print("Attempting to send message to", self.reporter_id)
        # print("Got recipient:", self.reporter, "from guild", self.guild)
        if not self.automated:
            await self.reporter.send(content=message_content)
        
    async def send_warning_message(self):
        await self.message.author.send("Spam is not tolerated on this service. Further unsolicited or abusive messages may result in a temporary or permanent ban from this service.")

    async def send_banning_message(self, ban_length):
        await self.message.author.send("You have been banned for " + str(ban_length) + " days.")

    async def send_permanent_banning_message(self):
        await self.message.author.send("You have been banned from using this platform")

    def report_complete(self):
        return self.state == State.COMPLETE or self.state == State.CANCELLED

    def report_cancled(self):
        return self.state == State.CANCELLED
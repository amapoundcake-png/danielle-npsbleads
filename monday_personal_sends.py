"""
monday_personal_sends.py — One-time personal follow-ups to Calendly clickers.

Run once on Monday July 6, 2026. These are warm leads who clicked the
Calendly link but did not book. Each email is personal, not templated.
"""

import logging
import sys
from email_sender import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s -- %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

SENDER_SIG = (
    "<strong>Danielle Adams</strong><br>"
    "hello@danniadams.me"
)

CALENDLY = "https://calendly.com/danielleadamsfl/15min"

PERSONAL_EMAILS = [
    {
        "to": "accounting@rmhccf.org",
        "org": "Ronald McDonald House Charities Central Florida",
        "profile": "nonprofit",
        "subject": "Re: Quick idea for Ronald McDonald House Charities Central Florida",
        "body": (
            "Hi,<br><br>"
            "I saw you took a look at my calendar earlier this week. Wanted to follow up personally "
            "in case timing was an issue or you had questions before committing to a call.<br><br>"
            "I have a few specific ideas for Ronald McDonald House around community visibility and "
            "supporter outreach that I think would be genuinely useful. It would only take 20 minutes "
            "and I'm happy to work around your schedule.<br><br>"
            f"<a href='{CALENDLY}'>Grab a time here</a> or just reply and we'll find something that works.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "info@adultliteracyleague.org",
        "org": "Adult Literacy League",
        "profile": "nonprofit",
        "subject": "Re: Outreach help for Adult Literacy League",
        "body": (
            "Hi,<br><br>"
            "I noticed you pulled up my calendar after my note. I wanted to reach back out personally "
            "in case I can answer anything before you decide whether a call makes sense.<br><br>"
            "Adult Literacy League is doing work that is genuinely hard to communicate externally, "
            "and that is exactly where I can help. I have a few specific ideas around outreach and "
            "community storytelling that I would love to walk you through.<br><br>"
            f"<a href='{CALENDLY}'>Grab a time here</a> or reply directly and we will find something.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "chf@covenanthousefl.org",
        "org": "Covenant House Florida",
        "profile": "nonprofit",
        "subject": "Re: Outreach and visibility for Covenant House Florida",
        "body": (
            "Hi,<br><br>"
            "I saw you opened my note a few times and checked my calendar. I wanted to follow up "
            "personally because I think there is a real opportunity here and I did not want it to "
            "get lost in the inbox shuffle.<br><br>"
            "Covenant House is doing critical work and I have specific ideas around how to tell that "
            "story in a way that moves supporters and funders. Even a 20-minute conversation would "
            "be worth your time.<br><br>"
            f"<a href='{CALENDLY}'>Grab a time here</a>, or just reply and I will make it easy.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "info@aspirehp.org",
        "org": "Aspire Health Partners",
        "profile": "nonprofit",
        "subject": "Re: Outreach and visibility for Aspire Health Partners Inc",
        "body": (
            "Hi,<br><br>"
            "I wanted to follow up personally. You checked my calendar twice after my note and I "
            "want to make sure I am not missing you.<br><br>"
            "I have a few ideas specifically for Aspire around community outreach and visibility that "
            "I think would resonate with the work you are already doing. Happy to keep it to 20 minutes "
            "and come with something concrete.<br><br>"
            f"<a href='{CALENDLY}'>Grab a time here</a> or reply and we will find something that works.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "jessica.guzman@cflhomeless.org",
        "org": "Coalition for the Homeless of Central Florida",
        "profile": "nonprofit",
        "subject": "Re: Quick idea for Coalition for the Homeless of Central Florida",
        "body": (
            "Hi Jessica,<br><br>"
            "I wanted to follow up personally after my note last week. I saw you looked at my calendar "
            "and did not want to assume the timing was wrong without checking in.<br><br>"
            "I have specific ideas for the Coalition around community engagement and outreach systems "
            "that could take some of the visibility work off your team's plate. It is a 20-minute call "
            "and I will come prepared.<br><br>"
            f"<a href='{CALENDLY}'>Grab a time here</a>, or just reply and we will figure out something that works.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "info@feedhopenow.org",
        "org": "Second Harvest Food Bank",
        "profile": "nonprofit",
        "subject": "Re: A few ideas for Second Harvest Food Bank",
        "body": (
            "Hi,<br><br>"
            "Just following up personally after my note from last week. I had a few specific ideas "
            "for Second Harvest around community storytelling and outreach that I would love to share.<br><br>"
            "You are feeding people. That story deserves to be told in a way that keeps supporters "
            "engaged and brings in new ones. I can help with that.<br><br>"
            f"Even a quick 20-minute call would be worth it. <a href='{CALENDLY}'>Grab a time here</a> "
            "or reply and I will work around your schedule.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "helpkids@hope.boystown.org",
        "org": "Boys Town Central Florida",
        "profile": "nonprofit",
        "subject": "Re: Outreach and visibility for Boys Town Central Florida",
        "body": (
            "Hi,<br><br>"
            "I saw you checked out my calendar after my note today. Wanted to follow up personally "
            "in case you had questions before committing to a call.<br><br>"
            "I have a few specific ideas for Boys Town around community visibility and outreach that "
            "I think would be worth 20 minutes of your time. Happy to come with something concrete.<br><br>"
            f"<a href='{CALENDLY}'>Grab a time here</a> or just reply and we will find something that works.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
    {
        "to": "info@habitatorlando.org",
        "org": "Habitat for Humanity Greater Orlando",
        "profile": "nonprofit",
        "subject": "Re: A few ideas for Habitat for Humanity Greater Orlando",
        "body": (
            "Hi,<br><br>"
            "Following up on my note from last week. I have a few specific ideas for Habitat around "
            "community visibility and outreach that I think would be useful given the scale of what "
            "you are building locally.<br><br>"
            "Happy to keep it to 20 minutes and come with something concrete rather than vague.<br><br>"
            f"<a href='{CALENDLY}'>Grab a time here</a>, or just reply and we will find something "
            "that works for your schedule.<br><br>"
            f"{SENDER_SIG}"
        ),
    },
]


def run():
    logger.info("=== MONDAY PERSONAL SENDS: %d emails ===", len(PERSONAL_EMAILS))
    sent = 0
    failed = 0
    for item in PERSONAL_EMAILS:
        success = send_email(
            to_address=item["to"],
            subject=item["subject"],
            body=item["body"],
            profile=item["profile"],
            is_html=True,
            respect_rate_limit=True,
            org=item["org"],
        )
        if success:
            logger.info("Sent to %s (%s)", item["org"], item["to"])
            sent += 1
        else:
            logger.error("Failed: %s (%s)", item["org"], item["to"])
            failed += 1

    logger.info("=== DONE: sent %d, failed %d ===", sent, failed)


if __name__ == "__main__":
    run()

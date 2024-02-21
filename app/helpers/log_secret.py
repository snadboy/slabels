import logging
logger = logging.getLogger(__name__)
from app.helpers.config import Config


class SecretFilter(logging.Filter):
    def filter(self, record):
        redacts = ["PLEX_TOKEN", "SONARR_API_KEY"]

        for redact in redacts:
            redact = Config.__dict__.get(redact)
            if redact in record.msg:
                record.msg = record.msg.replace(redact, "********")
        return True

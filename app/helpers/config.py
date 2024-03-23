import logging
from typing import Dict

logger = logging.getLogger(__name__)


class Config:
    PLEX_URL = None
    PLEX_TOKEN = None

    SONARR_URL = None
    SONARR_API_KEY = None

    SYNC_INTERVAL_MINS = None

    LOGGING_LEVEL = logging.INFO

    HEADERS_PLEX = {}
    HEADERS_SONARR = {}
    HEADERS_ALL = {}

    @staticmethod
    def initialize():
        Config.HEADERS_PLEX = Config.headers('HEADERS_PLEX')
        Config.HEADERS_SONARR = Config.headers('HEADERS_SONARR')
        Config.HEADERS_ALL = Config.headers('HEADERS_ALL')
        Config.PLEX_URL = os.getenv("PLEX_URL", '')
        Config.PLEX_TOKEN = os.getenv("PLEX_TOKEN", '')
        Config.SONARR_URL = os.getenv("SONARR_URL", '')
        Config.SONARR_API_KEY = os.getenv("SONARR_API_KEY", '')
        Config.SYNC_INTERVAL_MINS = int(os.getenv("SYNC_INTERVAL_MINS", 5))
        Config.LOGGING_LEVEL = int(os.getenv("LOGGING_LEVEL", logging.INFO))

    @staticmethod
    def headers(prefix: str) -> Dict[str, str]:
        hdr_values = [value 
                        for key, value in os.environ.items() 
                        if key.startswith(prefix)]    
        return {header.split(':')[0]: header.split(':')[1] for header in hdr_values}

    @staticmethod
    def log_constants():
        constants = {
            attr: getattr(Config, attr)
            for attr in dir(Config)
            if not callable(getattr(Config, attr)) and not attr.startswith("__")
        }
        for key, value in constants.items():
            logging.info(f"Env:  {key}: {value}")


import os
Config.initialize()

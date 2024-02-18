import logging
logger = logging.getLogger(__name__)

class Config:
    PLEX_URL = None
    PLEX_TOKEN = None

    SONARR_URL = None
    SONARR_API_KEY = None

    MAX_THREADS = 5
    SYNC_INTERVAL_SECS = 60

    LOGGING_LEVEL = logging.INFO
    
    @staticmethod
    def initialize():
        import os
        Config.PLEX_URL = os.getenv('PLEX_URL')
        Config.PLEX_TOKEN = os.getenv('PLEX_TOKEN')
        Config.SONARR_URL = os.getenv('SONARR_URL')
        Config.SONARR_API_KEY = os.getenv('SONARR_API_KEY')

    @staticmethod
    def log_constants():
        constants = {attr: getattr(Config, attr) for attr in dir(Config) if not callable(getattr(Config, attr)) and not attr.startswith("__")}
        for key, value in constants.items():
            logging.info(f"{key}: {value}")

Config.initialize()

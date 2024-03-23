import logging
logger = logging.getLogger(__name__)

from datetime import datetime as dt
from datetime import timedelta
from typing import Any, Dict, List, Optional
from requests import Session
from arrapi import Series, SonarrAPI, Tag

from app.helpers.config import Config


class SonarrFuncs:
    def __init__(self):
        try:
            session = Session()
            for key, value in Config.HEADERS_SONARR.items():
                session.headers[key] = value
            for key, value in Config.HEADERS_ALL.items():
                session.headers[key] = value
                
            self.api = SonarrAPI(Config.SONARR_URL, Config.SONARR_API_KEY, session=session)
        except Exception as e:
            logger.exception(e)
            raise e

    def sonarr_all_series(self) -> Dict[str, Series]:
        return {str(series.title): series for series in self.api.all_series()}

    def sonarr_all_tags(self) -> list[Tag]:
        return self.api.all_tags()

    def sonarr_all_tags_by_id(self):
        return {str(tag.id): tag.label for tag in self.sonarr_all_tags()}

    def sonarr_all_tags_by_label(self):
        return {tag.label: str(tag.id) for tag in self.sonarr_all_tags()}

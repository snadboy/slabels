import logging
logger = logging.getLogger(__name__)

from datetime import datetime as dt
from datetime import timedelta
from typing import Any, Dict, List, Optional

from arrapi import Series, SonarrAPI, Tag

from config import Config


class SonarrFuncs:
    def __init__(self):
        self.api = SonarrAPI(Config.SONARR_URL, Config.SONARR_API_KEY)

    def sonarr_all_series(self) -> Dict[str, Series]:
        return {str(series.title): series for series in self.api.all_series()}

    def sonarr_all_tags(self) -> list[Tag]:
        return self.api.all_tags()

    def sonarr_all_tags_by_id(self):
        return {str(tag.id): tag.label for tag in self.sonarr_all_tags()}

    def sonarr_all_tags_by_label(self):
        return {tag.label: str(tag.id) for tag in self.sonarr_all_tags()}

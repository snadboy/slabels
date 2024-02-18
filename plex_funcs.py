import logging
logger = logging.getLogger(__name__)

from datetime import datetime as dt
from datetime import timedelta
from typing import Any, Dict, List, Optional

from plexapi.library import LibrarySection
from plexapi.server import PlexServer

from config import Config


class PlexFuncs:
    def __init__(self):
        self.api = PlexServer(Config.PLEX_URL, Config.PLEX_TOKEN)

    def plex_series_search(
        self, title: Optional[str] = None, days: Optional[int] = None
    ):
        # days - Number of days since TV Show added to Plex, e.g.
        #           if days = 30, search for shows added in the last 30 days
        # title - Title of show to match
        #           NOTE: searches are case insensitive AND will accept partial matches, e.g.
        #               'after' matches 'After The Flood' AND 'After Life'
        try:
            plex_tv_shows = self.api.library.section("TV Shows")
            advancedFilters = {"and": []}  # Match all of the following in this list
            if isinstance(days, int):
                d = dt.now() - timedelta(days=days + 1)
                advancedFilters["and"].append({"show.addedAt>>": d})
            if isinstance(title, str):
                advancedFilters["and"].append({"show.title": title})
            plex_series_list = plex_tv_shows.search(filters=advancedFilters)
        except Exception as e:
            logger.exception(e)
            raise e

        return [plex_series.title for plex_series in plex_series_list]

    def plex_tv_advanced_search(self, advancedFilters: Dict[str, Any]):
        plex_tv_shows: LibrarySection = self.api.library.section("TV Shows")
        return plex_tv_shows.search(filters=advancedFilters)

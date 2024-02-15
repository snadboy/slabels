from src.sblog import logger, logging
from plexapi.server import PlexServer
from arrapi import SonarrAPI, Series, Tag
from typing import Any, List, Dict, Optional
from datetime import datetime as dt, timedelta

__all__ = ["Shows"]
class Shows:
    def __init__(
        self, plex_url: str, plex_token: str, sonarr_url: str, sonarr_api_key: str
    ) -> None:
        self.plex_url = plex_url
        self.plex_token = plex_token
        plexapi_logger = logging.getLogger("plexapi")
        plexapi_logger.setLevel(logging.INFO)
        self.plex = PlexServer(self.plex_url, self.plex_token)

        self.sonarr_url = sonarr_url
        self.sonarr_api_key = sonarr_api_key
        arrapi_logger = logging.getLogger("arrapi")
        arrapi_logger.setLevel(logging.INFO)
        self.sonarr = SonarrAPI(self.sonarr_url, self.sonarr_api_key)

        # self._sonarr_series: Dict[str, Series] = {}

    @property
    def sonarr_series(self) -> Dict[str, Series]:
        return {str(series.title): series for series in self.sonarr.all_series()}

    # @property
    # def sonarr_series_with_tags(self) -> Dict[str, Series]:
    #     return {
    #         key: value
    #         for key, value in self.sonarr_series.items()
    #         if value is list and len(value.tags) > 0
    #     }

    @property
    def sonarr_tags_by_id(self):
        return {str(tag.id): tag.label for tag in self.sonarr_tags}

    @property
    def sonarr_tags(self) -> list[Tag]:
        return self.sonarr.all_tags()

    @property
    def sonarr_tags_by_label(self):
        return {tag.label: str(tag.id) for tag in self.sonarr_tags}

    def stp(self, sonarr_series_id):
        # Get sonarr series details from sonarr series id
        sonarr_series = self.sonarr.get_series(sonarr_series_id)

        # Get sonarr lables in this series
        sonarr_labels: set = set(
            tag.label for tag in self.sonarr.all_tags() if tag.id in sonarr_series.tags
        )

        # Get plex series details from sonarr series title
        plex_tv_shows = self.plex.library.section("TV Shows")
        plex_series = plex_tv_shows.search(title=sonarr_series.title)
        if len(plex_series) == 0:
            logger.error(f"Series '{sonarr_series.title}' was not found in Plex")
            return
        if not plex_series[0].isFullObject():
            plex_series[0].reload(checkFiles=False, deep=False)

        # Get current labels from the plex_series
        plex_labels: set = set(label.tag.lower() for label in plex_series[0].labels)

        # Add Sonarr labels that are not it Plex labels
        labels_to_add = sonarr_labels - plex_labels
        if len(labels_to_add) > 0:
            plex_series.addLabel(list(labels_to_add))
            logger.info(
                f'Added labels, [{", ".join(labels_to_add)}], to Plex series, {plex_series.title}'
            )

        # Remove Plex labels that are not in Sonarr labels
        labels_to_remove = plex_labels - sonarr_labels
        if len(labels_to_remove) > 0:
            plex_series.removeLabel(list(labels_to_remove))
            logger.info(
                f'Removed labels, [{", ".join(labels_to_remove)}], from Plex series, {plex_series.title}'
            )

        # # Get the tags for the series from Sonarr
        # sonarr_tags = self.sonarr_series[plex_series.title].tags

        # Convert tag IDs to labels using the tag dictionary
        # sonarr_labels = set()
        # if isinstance(sonarr_tags, list):
        #     sonarr_labels = {
        #         str(sonarr_tags_dict[tag.id]).lower()
        #             for tag in sonarr_tags
        #             if tag.id in sonarr_tags_dict
        #     }

        # # Get current labels from the plex_series
        # plex_labels = {label.tag.lower() for label in plex_series.labels}

        # # Add Sonarr labels that are not it Plex labels
        # labels_to_add = sonarr_labels - plex_labels
        # if len(labels_to_add) > 0:
        #     plex_series.addLabel(list(labels_to_add))
        #     print(
        #         f'  Added labels [{", ".join(labels_to_add)}] to {plex_series.title}'
        #     )

        # # Remove Plex labels that are not in Sonarr labels
        # labels_to_remove = plex_labels - sonarr_labels
        # if len(labels_to_remove) > 0:
        #     plex_series.removeLabel(list(labels_to_remove))
        #     print(
        #         f'  Removed labels [{", ".join(labels_to_remove)}] from {plex_series.title}'
        #     )

    def plex_series_search(self, title: Optional[str]=None, days: Optional[int]=None):
        # days - Number of days since TV Show added to Plex, e.g.
        #           if days = 30, search for shows added in the last 30 days
        # title - Title of show to match
        #           NOTE: searches are case insensitive AND will accept partial matches, e.g.
        #               'after' matches 'After The Flood' AND 'After Life'
        try:
            plex_tv_shows = self.plex.library.section("TV Shows")
            advancedFilters = {
                            'and': [                            # Match all of the following in this list
                            ]
                        }
            if (isinstance(days, int)):
                d = (dt.now() - timedelta(days=days + 1))
                advancedFilters['and'].append({'show.addedAt>>': d})
            if (isinstance(title, str)):
                advancedFilters['and'].append({'show.title':title})
            plex_series_list = plex_tv_shows.search(filters=advancedFilters)
        except Exception as e:
            logger.exception(e)
            raise e

        return [plex_series.title for plex_series in plex_series_list]
    
    def sonarr_to_plex_batch(self, days: Optional[int]=None, title: Optional[str]=None):
        # days - Number of days since TV Show added to Plex, e.g.
        #           if days = 30, search for shows added in the last 30 days
        # title - Title of show to match
        #           NOTE: searches are case insensitive AND will accept partial matches, e.g.
        #               'after' matches 'After The Flood'

        def result(error: bool=False, message: str='', matches: List[str]=[]) -> {Any, Any}:
            return {
                'status': {
                    'error': error,
                    'message': message
                },
                'search': {
                    'days': days,
                    'title': title,
                    'matches': matches
                },
                'changes': []
            }
        def result_add_labels(result: List[{str, Any}], title: str='None', added: List[str]=[], deleted: List[str]=[]) -> None:
            result['changes'].append({
                    title: {
                            'added': added,
                            'deleted': deleted
                        }
                })
        
        # Get list of Plex series to process
        try:
            plex_tv_shows = self.plex.library.section("TV Shows")
            advancedFilters = {
                            'and': [                            # Match all of the following in this list
                            ]
                        }
            if (isinstance(days, int) and days > 0):
                d = (dt.now() - timedelta(days=days + 1))
                advancedFilters['and'].append({'show.addedAt>>': d})
            if (isinstance(title, str) and title):
                advancedFilters['and'].append({'show.title':title})
            plex_series_list = plex_tv_shows.search(filters=advancedFilters)
        except Exception as e:
            logger.exception(e)
            return result(error=True, message=e)

        if (len(plex_series_list) == 0):
            return result(message='No Plex series matched search criteria')

        sonarr_series = self.sonarr_series

        # Create a dictionary mapping Sonarr tag IDs to labels
        tag_dict = {tag.id: tag.label for tag in self.sonarr_tags}

        # Iterate over selected series in Plex
        r = result() # matches=[plex_series.title for plex_series in plex_series_list])
        for plex_series in plex_series_list:
            # Check if the series exists in Sonarr
            if plex_series.title in sonarr_series:
                # logger.info(f"Processing: {plex_series.title}")

                # Get the tags for the series from Sonarr
                sonarr_tags = sonarr_series[plex_series.title].tags

                # Convert tag IDs to labels using the tag dictionary
                sonarr_labels = set()
                if isinstance(sonarr_tags, list):
                    sonarr_labels = {
                        str(tag_dict[tag.id]).lower()
                        for tag in sonarr_tags
                        if tag.id in tag_dict
                    }

                # Get current labels from the plex_series
                plex_labels = {label.tag.lower() for label in plex_series.labels}

                # Add Sonarr labels that are not it Plex labels
                labels_to_add = sonarr_labels - plex_labels
                if len(labels_to_add) > 0:
                    plex_series.addLabel(list(labels_to_add))
                    # logger.info(
                    #     f'Added labels [{", ".join(labels_to_add)}] to {plex_series.title}'
                    # )

                # Remove Plex labels that are not in Sonarr labels
                labels_to_remove = plex_labels - sonarr_labels
                if len(labels_to_remove) > 0:
                    plex_series.removeLabel(list(labels_to_remove))
                    # logger.info(
                    #     f'Removed labels [{", ".join(labels_to_remove)}] from {plex_series.title}'
                    # )
                # else:
                #     logger.info(f"No labels to process: {plex_series.title}")
                    
                if (len(labels_to_add) > 0 or len(labels_to_remove) > 0):
                    result_add_labels(r, title=plex_series.title, added=labels_to_add, deleted=labels_to_remove)

        return r

    def plex_to_sonarr(self):
        plex_shows = self.plex.library.section("TV Shows").search(libtype="show")
        for plex_show in plex_shows:
            # Ensure we have all the genres associated with this show
            if not plex_show.isFullObject():
                plex_show.reload(checkFiles=False, deep=False)

            # Determine which tags we want to copy from Plex to Sonarr for this show
            tags_to_add = {
                genre.tag[3:].lower().replace(" ", "")
                for genre in plex_show.genres
                if genre.tag.lower().startswith("sb_")
            }

            # No tags to copy, skip to the next show
            if len(tags_to_add) == 0:
                continue

            # Add any tags that are not yet in Sonarr
            for tag in tags_to_add:
                if tag not in self.sonarr_tags_by_label:
                    self.sonarr.create_tag(tag)

            sonarr_shows = self.sonarr.search_series(f'"{plex_show.title}"')
            for sonarr_show in sonarr_shows:
                # The search_series method can return multiple matches - use the first exact title match that is a sonarr show
                if (
                    isinstance(sonarr_show, Series)
                    and sonarr_show.id != None
                    and sonarr_show.title == sonarr_show.title
                ):
                    # If the sonarr_show has existing tags, remove those from the tags_to_add list
                    if sonarr_show.tags is list:
                        show_tags = [tag.label for tag in sonarr_show.tags]
                        tags_to_add = list(set(tags_to_add) - set(show_tags))

                    # If there are still tags_to_add, update the sonarr_show by adding them
                    if len(tags_to_add) > 0:
                        sonarr_show.edit(tags=list(tags_to_add), apply_tags="add")
                        print(
                            f'Added tags: [{", ".join(tags_to_add)}] to {sonarr_show.title}'
                        )
                    break

        print("")

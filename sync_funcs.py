import logging

logger = logging.getLogger(__name__)

from datetime import datetime as dt
from datetime import timedelta
from typing import Any, Dict, List, Optional

from plexapi.video import Show

from plex_funcs import PlexFuncs
from sonarr_funcs import SonarrFuncs


def sonarr_to_plex(days: Optional[int] = None, title: Optional[str] = None):
    # days - Number of days since TV Show added to Plex, e.g.
    #           if days = 30, search for shows added in the last 30 days
    # title - Title of show to match
    #           NOTE: searches are case insensitive AND will accept partial matches, e.g.
    #               'after' matches 'After The Flood'

    logger.info("Syncing Sonarr tags -> Plex labels")

    # Helper function to create/populate a result dictionary
    def result_create(
        error: bool = False, message: str = "", matches: List[str] = []
    ) -> {str, Any}:
        return {
            "status": {"error": error, "message": message},
            "search": {"days": days, "title": title, "matches": matches},
            "changes": [],
        }

    def result_add_changes(
        result: {str, Any}, title: str, added: List[str], deleted: List[str]
    ) -> None:
        if len(added) > 0 or len(deleted) > 0:
            result["changes"].append({title: {"added": added, "deleted": deleted}})

    plex: PlexFuncs = PlexFuncs()
    sonarr: SonarrFuncs = SonarrFuncs()

    # Get list of Plex shows to process
    try:
        advancedFilters: Dict[str, List] = {
            "and": []
        }  # Match all of the following in this list
        if days and days > 0:
            d = dt.now() - timedelta(days=days + 1)
            advancedFilters["and"].append({"show.addedAt>>": d})
        if title:
            advancedFilters["and"].append({"show.title": title})

        if len(plex_shows := plex.plex_tv_advanced_search(advancedFilters)) == 0:
            return result_create(message="No Plex shows matched search criteria")

        sonarr_series = sonarr.sonarr_all_series()

        # Create a dictionary mapping Sonarr tag IDs to labels
        tag_dict = {tag.id: tag.label for tag in sonarr.sonarr_all_tags()}

        result = result_create()
        for plex_show in plex_shows:
            if plex_show.title in sonarr_series:
                # Get show's tags from Sonarr
                sonarr_tags = sonarr_series[plex_show.title].tags

                # Convert tag IDs to labels using the tag dictionary
                sonarr_labels = set()
                if isinstance(sonarr_tags, list):
                    sonarr_labels = {
                        str(tag_dict[tag.id]).lower()
                        for tag in sonarr_tags
                        if tag.id in tag_dict
                    }

                plex_labels = {label.tag.lower() for label in plex_show.labels}

                # Add Sonarr labels that are not it Plex labels
                # labels_to_add = sonarr_labels - plex_labels
                if len(labels_to_add := list(sonarr_labels - plex_labels)) > 0:
                    plex_show.addLabel(labels_to_add)

                # Remove Plex labels that are not in Sonarr labels
                if len(labels_to_remove := list(plex_labels - sonarr_labels)) > 0:
                    plex_show.removeLabel(labels_to_remove)

                result_add_changes(
                    result=result,
                    title=plex_show.title,
                    added=labels_to_add,
                    deleted=labels_to_remove,
                )

        logger.info(f"Sonarr to Plex sync results: {result}")
        return result
    except Exception as e:
        logger.exception(f"Sonarr to Plex EXCEPTION: {e}")
        return result_create(error=True, message=e)


def plex_to_sonarr():
    plex = PlexFuncs()
    sonarr = SonarrFuncs()

    plex_shows = plex.library.section("TV Shows").search(libtype="show")
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
            if tag not in sonarr.sonarr_tags_by_label:
                sonarr.create_tag(tag)

        sonarr_shows = sonarr.search_series(f'"{plex_show.title}"')
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

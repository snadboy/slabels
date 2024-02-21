import logging

logger = logging.getLogger(__name__)

import asyncio
from datetime import datetime as dt
from datetime import timedelta
from typing import Any, Dict, List, Optional

from plexapi.video import Show

from app.services.plex import PlexFuncs
from app.services.sonarr import Series, SonarrFuncs, Tag

semaphore_sync = asyncio.Semaphore(5)


def sonarr_to_plex_thread(
    plex_show: Show, sonarr_series: Dict[str, Series], tag_dict: Dict[int, str]
) -> {str, Any}:
    changes: List[Dict[str, Any]] = None

    # Get show's tags from Sonarr
    sonarr_labels = {
        str(tag_dict[tag.id]).lower()
        for tag in (sonarr_series[plex_show.title].tags or [])
        if tag.id in tag_dict
    }

    plex_labels = {label.tag.lower() for label in plex_show.labels}

    if len(labels_to_add := list(sonarr_labels - plex_labels)) > 0:
        plex_show.addLabel(labels_to_add)
    if len(labels_to_remove := list(plex_labels - sonarr_labels)) > 0:
        plex_show.removeLabel(labels_to_remove)

    if len(labels_to_add) > 0 or len(labels_to_remove) > 0 :
        changes = {plex_show.title: {"added": labels_to_add, "removed": labels_to_remove}}

    return changes

async def sonarr_to_plex_task(plex_show: Show, sonarr_series: Dict[str, Series], tag_dict: Dict[int, str]) -> {str, Any}:
    async with semaphore_sync:
        return await asyncio.to_thread(sonarr_to_plex_thread, plex_show, sonarr_series, tag_dict)

async def sonarr_to_plex(days: Optional[int] = None, title: Optional[str] = None):
    # days - Number of days since TV Show added to Plex, e.g.
    #           if days = 30, search for shows added in the last 30 days
    # title - Title of show to match
    #           NOTE: searches are case insensitive AND will accept partial matches, e.g.
    #               'after' matches 'After The Flood'

    logger.info("Syncing: Sonarr tags -> Plex labels")
    result = {"status": {"error": False, "message": ""}, "search": {"days": days, "title": title}, "changes": []}
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
            result["message"] = "No Plex shows matched search criteria"
            return result

        sonarr_series = sonarr.sonarr_all_series()
        tag_dict = {tag.id: tag.label for tag in sonarr.sonarr_all_tags()}
        pending = set(
            [
                asyncio.create_task(sonarr_to_plex_task(plex_show, sonarr_series, tag_dict))
                for plex_show in plex_shows
                if plex_show.title in sonarr_series
            ]
        )

        while True:
            results, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED, timeout=2.0)

            for task in results:
                try:
                    if (task_result := task.result()) is not None:
                        result["changes"].append(task.result())
                except Exception as e:
                    logger.exception(f"Sonarr to Plex EXCEPTION: {e}")

            if not pending:
                break

        if len(result["changes"]) == 0:
            result["status"]["message"] = "No changes made"

        logger.info(f"Results: Sonarr tags -> Plex labels {result}")
        return result
    except Exception as e:
        logger.exception(f"Sonarr to Plex EXCEPTION: {e}")
        result["status"] = {"error": True, "message": e}
        return result


# def plex_to_sonarr():
#     plex = PlexFuncs()
#     sonarr = SonarrFuncs()

#     plex_shows = plex.library.section("TV Shows").search(libtype="show")
#     for plex_show in plex_shows:
#         # Ensure we have all the genres associated with this show
#         if not plex_show.isFullObject():
#             plex_show.reload(checkFiles=False, deep=False)

#         # Determine which tags we want to copy from Plex to Sonarr for this show
#         tags_to_add = {
#             genre.tag[3:].lower().replace(" ", "")
#             for genre in plex_show.genres
#             if genre.tag.lower().startswith("sb_")
#         }

#         # No tags to copy, skip to the next show
#         if len(tags_to_add) == 0:
#             continue

#         # Add any tags that are not yet in Sonarr
#         for tag in tags_to_add:
#             if tag not in sonarr.sonarr_tags_by_label:
#                 sonarr.create_tag(tag)

#         sonarr_shows = sonarr.search_series(f'"{plex_show.title}"')
#         for sonarr_show in sonarr_shows:
#             # The search_series method can return multiple matches - use the first exact title match that is a sonarr show
#             if (
#                 isinstance(sonarr_show, Series)
#                 and sonarr_show.id != None
#                 and sonarr_show.title == sonarr_show.title
#             ):
#                 # If the sonarr_show has existing tags, remove those from the tags_to_add list
#                 if sonarr_show.tags is list:
#                     show_tags = [tag.label for tag in sonarr_show.tags]
#                     tags_to_add = list(set(tags_to_add) - set(show_tags))

#                 # If there are still tags_to_add, update the sonarr_show by adding them
#                 if len(tags_to_add) > 0:
#                     sonarr_show.edit(tags=list(tags_to_add), apply_tags="add")
#                     print(
#                         f'Added tags: [{", ".join(tags_to_add)}] to {sonarr_show.title}'
#                     )
#                 break

#     print("")

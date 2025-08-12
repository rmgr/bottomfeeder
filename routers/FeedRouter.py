from typing import Annotated
from fastapi import APIRouter, Depends, status
from services.FeedService import FeedService
from services.EntryService import EntryService
from services.AccountService import (get_current_user)
from models.Account import AccountSummary
from models.Pagination import PaginationParams
from models.requests.CreateFeedRequest import CreateFeedRequest
import uuid
FeedRouter = APIRouter(prefix="/v1/feed", tags=["feed"])


@FeedRouter.get("/", status_code=status.HTTP_200_OK)
def index(
    current_user: Annotated[AccountSummary, Depends(get_current_user)],
    feed_service: FeedService = Depends(),
    pagination: PaginationParams = Depends(),
):
    return feed_service.ListFeeds(current_user.id, pagination)


@FeedRouter.get("/{feed_id}/entries", status_code=status.HTTP_200_OK)
def list_entries(
    feed_id: uuid.UUID,
    current_user: Annotated[AccountSummary, Depends(get_current_user)],
    entry_service: EntryService = Depends(),
    pagination: PaginationParams = Depends(),
):
    return entry_service.ListEntries(feed_id, current_user.id, pagination)


@FeedRouter.post("/", status_code=status.HTTP_201_CREATED)
def create_feed(
    request: CreateFeedRequest,
    current_user: Annotated[AccountSummary, Depends(get_current_user)],
    feed_service: FeedService = Depends(),
):
    return feed_service.create_feed(request.feed_name,
                                    request.feed_url,
                                    current_user.id,
                                    request.crawl_interval,
                                    request.age_window)

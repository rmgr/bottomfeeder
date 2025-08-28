from typing import Annotated
from fastapi import APIRouter, Depends, status
from services.EntryService import EntryService
from services.AccountService import (get_current_user)
from models.Account import AccountSummary
from models.Pagination import PaginationParams
from models.requests.CreateEntryRequest import CreateEntryRequest

EntryRouter = APIRouter(prefix="/v1/entries", tags=["entry"])


@EntryRouter.get("/", status_code=status.HTTP_200_OK)
def index(
    current_user: Annotated[AccountSummary, Depends(get_current_user)],
    entry_service: EntryService = Depends(),
    pagination: PaginationParams = Depends(),
):
    return entry_service.ListEntries(current_user.id, pagination)


@EntryRouter.post("/", status_code=status.HTTP_201_CREATED)
def create_entry(
    request: CreateEntryRequest,
    current_user: Annotated[AccountSummary, Depends(get_current_user)],
    entry_service: EntryService = Depends(),
):
    return entry_service.create_entry(feed_id=request.fee_id,
                                      title=request.title,
                                      link=request.link,
                                      description=request.description,
                                      publish_date=request.publish_date
                                      )


@EntryRouter.get("/{entry_id}/unread", status_code=status.HTTP_200_OK)
async def unread_entry(
    entry_id: str,
    current_user: Annotated[AccountSummary | None, Depends(get_current_user)],
    entry_service: EntryService = Depends(),
):

    entry_service.mark_unread(entry_id)


@EntryRouter.get("/{entry_id}/read", status_code=status.HTTP_200_OK)
async def unread_entry(
    entry_id: str,
    current_user: Annotated[AccountSummary | None, Depends(get_current_user)],
    entry_service: EntryService = Depends(),
):

    entry_service.mark_read(entry_id)

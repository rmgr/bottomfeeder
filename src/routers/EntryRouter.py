from typing import Annotated
from fastapi import APIRouter, Depends, status
from services.EntryService import EntryService
from services.AccountService import (try_get_current_user)
from models.Account import AccountSummary
from models.Pagination import PaginationParams
from models.requests.CreateEntryRequest import CreateEntryRequest

EntryRouter = APIRouter(prefix="/v1/entries", tags=["entry"])


@EntryRouter.get("/{entry_id}/unread", status_code=status.HTTP_200_OK)
async def unread_entry(
    entry_id: str,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    entry_service.mark_unread(entry_id)


@EntryRouter.get("/{entry_id}/read", status_code=status.HTTP_200_OK)
async def read_entry(
    entry_id: str,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    entry_service.mark_read(entry_id)

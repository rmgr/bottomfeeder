from typing import Annotated
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from services.FeedService import FeedService
from services.EntryService import EntryService
from services.AccountService import (try_get_current_user)
from models.Account import AccountSummary
from models.Pagination import PaginationParams
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid
WebRouter = APIRouter(tags=["web"])

templates = Jinja2Templates(directory="templates")


@WebRouter.get("/")
async def feeds(
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    feed_service: FeedService = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    if not current_user:
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    feeds = feed_service.ListFeeds(
        current_user.id, PaginationParams(page_size=page_size, page=page)
    )

    return templates.TemplateResponse(
        request=request,
        name="feeds.html",
        context={
            "feeds": feeds,
            "page_size": page_size
        }
    )


@WebRouter.get("/feed/{feed_id}", response_class=HTMLResponse)
async def entries(
    feed_id: uuid.UUID,
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    if not current_user:
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    entries = entry_service.ListEntries(
        feed_id,
        current_user.id,
        PaginationParams(page_size=page_size, page=page)
    )

    return templates.TemplateResponse(
        request=request,
        name="entries.html",
        context={
            "feed_id": feed_id,
            "entries": entries,
        }
    )


"""@WebRouter.get("/entries/{entry_id}", response_class=HTMLResponse)
async def entries(
    entry_id: uuid.UUID,
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
):
    if not current_user:
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    entries = entry_service.ListEntries(
        feed_id,
        current_user.id,
        PaginationParams(page_size=page_size, page=page)
    )

    return templates.TemplateResponse(
        request=request,
        name="entries.html",
        context={
            "feed_id": feed_id,
            "entries": entries,
        }
    )
    """

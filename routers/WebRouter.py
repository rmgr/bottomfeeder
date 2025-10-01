from typing import Annotated
from fastapi import APIRouter, Depends, Request, Query, status, Form, UploadFile, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from services.FeedService import FeedService
from services.EntryService import EntryService
from services.AccountService import AccountService
from services.AccountService import (try_get_current_user)
from services.RssService import RssService
from models.Account import AccountSummary
from models.Pagination import PaginationParams
from fastapi.templating import Jinja2Templates
import uuid
from datetime import timedelta
WebRouter = APIRouter(tags=["web"])

templates = Jinja2Templates(directory="templates")


@WebRouter.get("/register")
async def register_page(
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
):
    if current_user:
        # already logged in → redirect home
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={}
    )


@WebRouter.post("/register")
async def register_form(
    request: Request,
    account_service: AccountService = Depends(),
    account_name: str = Form(...),
    email_address: str = Form(...),
    password: str = Form(...),
):
    try:
        account_service.create_account(account_name, email_address, password)
    except ValidationError as ex:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "errors": ex.errors(),
                "account_name": account_name,
                "email_address": email_address,
            },
            status_code=422
        )

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)



@WebRouter.get("/login")
async def login_page(
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
):
    if current_user:
        # already logged in → redirect home
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


@WebRouter.post("/login")
async def login_form(
    request: Request,
    account_service: AccountService = Depends(),
    email_address: str = Form(...),
    password: str = Form(...),
):
    # Authenticate user
    user = account_service.login(email_address, password)

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Invalid email or password",
                "email_address": email_address,
            },
            status_code=401
        )

    # Create refresh token (long-lived, 30 days)
    session_id = account_service.create_session(user.id)

    # Create response with redirect
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Set session ID cookie
    redirect_response.set_cookie(
        key="session_id",
        value=str(session_id),
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=2592000  # 30 days in seconds
    )

    return redirect_response


@WebRouter.post("/logout")
async def logout(
    session_id: Annotated[str | None, Cookie()] = None,
    account_service: AccountService = Depends(),
):
    # Revoke the refresh token if we have a session
    if session_id:
        try:
            account_service.revoke_session(session_id)
        except (ValueError, Exception):
            pass

    # Create redirect response
    redirect_response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Clear all auth cookies
    redirect_response.delete_cookie(key="session_id")

    return redirect_response


@WebRouter.get("/logout")
async def logout_get(
    session_id: Annotated[str | None, Cookie()] = None,
    account_service: AccountService = Depends(),
):
    """GET endpoint for logout link"""
    return await logout(session_id, account_service)


@WebRouter.get("/feeds")
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


@WebRouter.get("/add-feed")
async def add_feed_page(
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
):
    if not current_user:
        print("no user")
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    return templates.TemplateResponse(
        request=request,
        name="add_feed.html",
        context={
            "feed_name_error": "",
            "feed_url_error": "",
            "age_window_error": ""
        }
    )

@WebRouter.get("/update-feed/{feed_id}")
async def update_feed_page(
    feed_id: uuid.UUID,
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    feed_service: FeedService = Depends(),
):
    if not current_user:
        print("no user")
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    feed = feed_service.get(
        feed_id,
        current_user.id
    )
    return templates.TemplateResponse(
        request=request,
        name="update_feed.html",
        context={
            "feed": feed,
            "feed_name_error": "",
            "feed_url_error": "",
            "age_window_error": ""
        }
    )


@WebRouter.get("/import-feeds")
async def import_feeds_page(
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
):
    if not current_user:
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    return templates.TemplateResponse(
        request=request,
        name="import_feeds.html",
        context={
            "feed_name_error": "",
            "feed_url_error": "",
            "age_window_error": ""
        }
    )


@WebRouter.post("/import-feeds")
async def import_feeds(file: UploadFile,
                       current_user: Annotated[AccountSummary, Depends(try_get_current_user)],
                       rss_service: RssService = Depends()
                       ):

    if not current_user:
        raise Exception
    raw_bytes = await file.read()

    # Convert to string (assuming UTF-8 text file, e.g. OPML/XML)
    text = raw_bytes.decode("utf-8")
    rss_service.import_opml(text, current_user.id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@WebRouter.post("/update-feed/{feed_id}", status_code=status.HTTP_201_CREATED)
def update_feed(
    feed_id: uuid.UUID,
    current_user: Annotated[AccountSummary, Depends(try_get_current_user)],
    feed_name: str = Form(...),
    feed_url: str = Form(...),
    age_window: int | None = Form(None),
    crawl_page_content: Annotated[str | None, Form()] = None,
    feed_service: FeedService = Depends(),
):
    if not current_user:
        raise Exception
    feed_service.update_feed(
        feed_id=feed_id,
        feed_name=feed_name,
        feed_url=feed_url,
        created_by=current_user.id,
        age_window=age_window,
        crawl_page_content=crawl_page_content is not None,
    )
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@WebRouter.post("/add-feed", status_code=status.HTTP_201_CREATED)
def create_feed(
    current_user: Annotated[AccountSummary, Depends(try_get_current_user)],
    feed_name: str = Form(...),
    feed_url: str = Form(...),
    age_window: int | None = Form(None),
    crawl_page_content: Annotated[str | None, Form()] = None,
    feed_service: FeedService = Depends(),
):
    if not current_user:
        raise Exception
    feed_service.create_feed(
        feed_name=feed_name,
        feed_url=feed_url,
        created_by=current_user.id,
        age_window=age_window,
        crawl_page_content = crawl_page_content is not None
    )
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@WebRouter.get("/feed/{feed_id}", response_class=HTMLResponse)
async def entries(
    feed_id: uuid.UUID,
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
    feed_service: FeedService = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    if not current_user:
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    feed = feed_service.get(feed_id, current_user.id)
    entries = entry_service.ListEntriesForFeed(
        feed_id,
        current_user.id,
        PaginationParams(page_size=page_size, page=page)
    )

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "feed": feed,
            "entries": entries,
        }
    )

@WebRouter.get("/", response_class=HTMLResponse)
async def entries(
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    if not current_user:
        return templates.TemplateResponse(request=request, name="login.html")

    entries = entry_service.ListUnreadEntries(
        current_user.id,
        PaginationParams(page_size=page_size, page=page)
    )

    return templates.TemplateResponse(
        name="entries.html",
        context={"request": request, "entries": entries},
    )


@WebRouter.get("/entry/{entry_id}", response_class=HTMLResponse)
async def entry(
    entry_id: str,
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
):
    if not current_user:
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    entry = entry_service.get_entry(
        entry_id,
    )
    entry_service.mark_read(entry_id)

    return templates.TemplateResponse(
        request=request,
        name="entry.html",
        context={
            "entry": entry,
        }
    )


@WebRouter.get("/entry/{entry_id}/unread", response_class=HTMLResponse)
async def unread_entry(
    entry_id: str,
    request: Request,
    current_user: Annotated[AccountSummary | None, Depends(try_get_current_user)],
    entry_service: EntryService = Depends(),
):
    if not current_user:
        return templates.TemplateResponse(
            request=request, name="login.html"
        )

    entry = entry_service.get_entry(
        entry_id,
    )
    entry_service.mark_unread(entry_id)

    return templates.TemplateResponse(
        request=request,
        name="entry.html",
        context={
            "entry": entry,
        }
    )

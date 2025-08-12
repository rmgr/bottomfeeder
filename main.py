from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.db import (create_db_and_tables, get_db_connection)
from config.settings import settings
from repositories.FeedRepository import FeedRepository
from repositories.EntryRepository import EntryRepository
from services.EntryService import EntryService
from routers.AccountRouter import AccountRouter
from routers.FeedRouter import FeedRouter
from routers.EntryRouter import EntryRouter
from apscheduler.schedulers.background import BackgroundScheduler
from services.RssService import RssService

app = FastAPI()
scheduler = BackgroundScheduler()


def refresh():
    db_gen = get_db_connection()   # this is a generator
    db = next(db_gen)              # get the actual Session object
    try:
        feed_repository = FeedRepository()
        entry_repository = EntryRepository()
        entry_service = EntryService(db, entry_repository)
        rss_service = RssService(db, feed_repository, entry_service)
        rss_service.RefreshFeeds()
    finally:
        try:
            db.close()
            db_gen.close()  # properly close generator (calls db.close())
        except Exception:
            pass


scheduler.add_job(refresh, 'interval', minutes=settings.REFRESH_INTERVAL)
scheduler.start()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(AccountRouter)
app.include_router(FeedRouter)
app.include_router(EntryRouter)

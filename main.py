from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.db import (create_db_and_tables, get_db_connection)
from config.settings import settings
from repositories.FeedRepository import FeedRepository
from repositories.EntryRepository import EntryRepository
from services.EntryService import EntryService
from routers.WebRouter import WebRouter
from routers.EntryRouter import EntryRouter
from apscheduler.schedulers.background import BackgroundScheduler
from services.RssService import RssService
from datetime import datetime, timedelta
import logging
from starlette.exceptions import HTTPException as StarletteHTTPException
from exceptions.handlers import custom_http_exception_handler, custom_500_handler 

app = FastAPI()
scheduler = BackgroundScheduler()

app.mount("/static", StaticFiles(directory="static"), name="static")


def stale():
    db_gen = get_db_connection()   # this is a generator
    db = next(db_gen)              # get the actual Session object
    try:
        feed_repository = FeedRepository()
        entry_repository = EntryRepository()
        entry_service = EntryService(db, entry_repository)
        rss_service = RssService(db, feed_repository, entry_repository, entry_service)
        rss_service.process_age_windows()
    finally:
        try:
            db.close()
            db_gen.close()  # properly close generator (calls db.close())
        except Exception:
            pass


scheduler.add_job(stale, 'interval', minutes=settings.STALE_INTERVAL, next_run_time=datetime.now() + timedelta(seconds=30))

def refresh():
    db_gen = get_db_connection()   # this is a generator
    db = next(db_gen)              # get the actual Session object
    try:
        feed_repository = FeedRepository()
        entry_repository = EntryRepository()
        entry_service = EntryService(db, entry_repository)
        rss_service = RssService(db, feed_repository, entry_repository, entry_service)
        rss_service.refresh_feeds()
    finally:
        try:
            db.close()
            db_gen.close()  # properly close generator (calls db.close())
        except Exception:
            pass


scheduler.add_job(refresh, 'interval', minutes=settings.REFRESH_INTERVAL, next_run_time=datetime.now() + timedelta(seconds=30))
scheduler.start()


@app.on_event("startup")
def on_startup():
    #create_db_and_tables()
    pass
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, custom_500_handler)  
app.include_router(WebRouter)
app.include_router(EntryRouter)
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper() , logging.INFO), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",datefmt="%Y-%m-%d %H:%M:%S")

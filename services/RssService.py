from fastapi import Depends
import feedparser
from config.db import (get_db_connection)
import requests
from sqlalchemy.orm import Session
from models.Feed import Feed, FeedCreate
from repositories.FeedRepository import FeedRepository
from repositories.EntryRepository import EntryRepository
from services.EntryService import EntryService
from datetime import datetime, timezone, timedelta 
from email.utils import parsedate_to_datetime
from readabilipy import simple_json_from_html_string
import hashlib
from opyml import OPML
import uuid
from dateutil import parser


def parse_opml_outlines(input):
    output = []
    for outline in input.outlines:
        output = output + parse_opml_outlines(outline)
        if outline.type == 'rss':
            output.append(outline)
    return output


def safe_content(tag):
    return (getattr(tag, "content", "") or "").strip()


def normalise_date(tag):
    raw = safe_content(tag)
    if not raw:
        return ""
    try:
        dt = parsedate_to_datetime(raw)
        # Always use UTC for consistency
        return dt.astimezone(tz=None).isoformat()
    except Exception:
        return raw  # fall back to original if parsing fails


def get_entry_uid(entry, feed_url: str) -> str:
    # Prefer guid/id if present
    guid = safe_content(getattr(entry, "guid", None))
    if guid:
        return guid
    eid = safe_content(getattr(entry, "id", None))
    if eid:
        return eid

    # Fall back to link
    link = safe_content(getattr(entry, "link", None))
    if link:
        return link

    # Last resort: hash a combo of fields, with normalised date
    unique_string = (
        feed_url +
        safe_content(getattr(entry, "title", None)) +
        link +
        normalise_date(getattr(entry, "pub_date", None))
    )
    return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()


class RssService:
    db: Session
    feed_repository: FeedRepository
    entry_repository: EntryRepository
    entry_service: EntryService

    def __init__(self,
                 db: Session = Depends(get_db_connection),
                 feed_repository: FeedRepository = Depends(),
                 entry_repository: EntryRepository = Depends(),
                 entry_service: EntryService = Depends()):
        self.db = db
        self.feed_repository = feed_repository
        self.entry_repository = entry_repository
        self.entry_service = entry_service

    def ImportOpml(self, opml: str, created_by: uuid.UUID):
        document = OPML.from_xml(opml)
        feeds = parse_opml_outlines(document.body)
        for feed in feeds:
            feed_create = FeedCreate(feed_name=feed.title,
                                     feed_url=feed.xml_url,
                                     created_by=created_by)
            self.feed_repository.create(feed_create, self.db)
        self.db.commit()

    def RefreshFeeds(self, page_number: int = 1):
        page_size = 10
        feeds, total = self.feed_repository.list(
            self.db, page_number, page_size)
        for feed in feeds:
            self.RefreshFeed(feed)

        if total/page_size > page_number:
            self.RefreshFeeds(page_number + 1)

    def process_age_windows(self):
        page = 1
        page_size = 100

        while True:
            entries, total_count = self.entry_repository.list_all_entries(
                True, self.db, page, page_size
            )
            if not entries:  # no more entries
                break

            for entry in entries:
                self.process_age_window(entry)

            page += 1  
            self.db.commit()


    def process_age_window(self, entry):
        age_cutoff = entry.publish_date + timedelta(hours=entry.feed.age_window) 
        if age_cutoff > datetime.now():
            entry.is_read = True
            self.entry_repository.update(entry, self.db)
            print(f"cutting off {entry.title}") 

    def RefreshFeed(self, feed):
        try:
            response = requests.get(feed.feed_url, timeout=15)
            response.raise_for_status()
        except Exception as err:
            print(f"error fetching feed: {feed.feed_url}")
            print(err)
            return
        try:

            rss = feedparser.parse(response.content)

            if rss.bozo:  # bozo flag is set when parsing error occurs
                print(f"error parsing feed: {feed.feed_url}")
                print(rss.bozo_exception)
                return

            for entry in rss.entries:
                # Try to extract description safely
                description = ""
                if "summary" in entry:
                    article = simple_json_from_html_string(
                        entry.summary, use_readability=True
                    )
                    if article.get("plain_text"):
                        description = "\n".join(t["text"]
                                                for t in article["plain_text"])

                # Extract publication date
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = parser.parse(entry.published)
                else:
                    pub_date = datetime.now(timezone.utc)

                # Use entry.id if present, else fallback to link
                entry_uid = get_entry_uid(entry, entry.get("link"))

                self.entry_service.create_entry(
                    feed.id,
                    entry_uid,
                    entry.get("title", "No title"),
                    entry.get("link"),
                    description,
                    pub_date,
                )
        except Exception as err:
            print(f"error parsing feed: {feed.feed_url}")
            print(err)
            return

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
import logging
import time
import traceback
from bs4 import BeautifulSoup

def safe_extract_text(html: str):
    # 1) Try ReadabiliPy (best quality)
    try:
        result = simple_json_from_html_string(html, use_readability=True)
        if isinstance(result, dict):
            # plain_text is a list of {text: "..."} objects
            pt = result.get("plain_text")
            if pt:
                return "\n".join(t["text"] for t in pt if "text" in t)
            # fallback to content
            content = result.get("content")
            if content:
                return BeautifulSoup(content, "html.parser").get_text(" ", strip=True)
    except Exception:
        logging.exception("ReadabiliPy failed")

    # 2) Fallback: BeautifulSoup from original HTML
    try:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        if text:
            return text
    except Exception:
        logging.exception("BeautifulSoup fallback failed")

    # 3) Last resort: return raw HTML truncated
    return html[:2000]  # prevent massive blobs
def parse_opml_outlines(node):
    output = []

    # Recurse into children if present
    child_outlines = getattr(node, "outlines", None)
    if child_outlines:
        for child in child_outlines:
            output.extend(parse_opml_outlines(child))

    # Detect any feed with xmlUrl (covers RSS, Atom, RDF)
    xml_url = getattr(node, "xml_url", None) or getattr(node, "xmlUrl", None)
    if xml_url:
        output.append(node)

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

    def import_opml(self, opml: str, created_by: uuid.UUID):
        document = OPML.from_xml(opml)
        feeds = parse_opml_outlines(document.body)

        
        # Deduplicate feeds by feed_url (keep first occurrence)
        unique_feeds_dict = {}
        for feed in feeds:
            if feed.xml_url not in unique_feeds_dict:
                unique_feeds_dict[feed.xml_url] = feed
        unique_feeds = list(unique_feeds_dict.values())

        # Extract feed URLs from OPML
        feed_urls = [feed.xml_url for feed in unique_feeds]

        # Get existing feeds using the repository method
        existing_feed_urls = set(self.feed_repository.get_existing_feeds(feed_urls, created_by, self.db))
        logging.info(existing_feed_urls)

        # Insert only feeds that are not already in the database
        for feed in unique_feeds:
            if feed.xml_url in existing_feed_urls:
                continue  # skip existing feeds\
            try:
                feed_create = FeedCreate(feed_name=feed.title,
                                     feed_url=feed.xml_url,
                                     created_by=created_by)
                self.feed_repository.create(feed_create, self.db)
            except Exception as ex:
                logging.info("Failed to import feed")
                logging.info(ex)
                self.db.rollback()
                self.db.begin()
        self.db.commit()


    def process_age_windows(self):
        page = 1
        page_size = 100
        logging.info("Starting to process age windows")
        while True:
            entries, total_count = self.entry_repository.list_all_entries(
                False, self.db, page, page_size
            )
            if len(entries) == 0:  # no more entries
                break

            for entry in entries:
                self.process_age_window(entry)

            page += 1
            logging.info(page)
            ## TODO is this writing the unchanged records back to the db??
        self.db.commit()
        logging.info("Finished processing age windows")


    def process_age_window(self, entry):
        age_cutoff = entry.publish_date + timedelta(hours=entry.feed.age_window) 
        if age_cutoff < datetime.now():
            entry.is_read = True
            self.entry_repository.update(entry, self.db)
            logging.info(f"cutting off {entry.title}") 


    def refresh_feeds(self):
        page = 1
        page_size = 10
        while True:
            feeds, total = self.feed_repository.list(
                self.db, page, page_size)
            if not feeds:
                break
            for feed in feeds:
                self.refresh_feed(feed)
            page += 1


    def refresh_feed(self, feed):
        headers = {
            "User-Agent": "bottomfeeder-rss/1.0 (+https://wiki.rmgr.dev)"
        }
        try:
            response = requests.get(feed.feed_url, timeout=15, headers=headers)
            response.raise_for_status()
        except Exception as err:
            logging.error(f"error fetching feed: {feed.feed_url}")
            logging.error(err)
            return
        try:

            rss = feedparser.parse(response.content)

            if rss.bozo:  # bozo flag is set when parsing error occurs
                logging.error(f"error parsing feed: {feed.feed_url}. Trying to extract anyway.")
                logging.error(rss.bozo_exception)
            for entry in rss.entries:
                
                # Try to extract description safely
                description = ""
                if "summary" in entry:
                    description = safe_extract_text(entry.summary)

                entry_uid = get_entry_uid(entry, entry.get("link"))
                # Extract page body if requested
                if feed.crawl_page_content:
                    exists = self.entry_service.exists(entry_uid)
                    if not exists:
                        response = requests.get(entry.get("link"), timeout=15, headers=headers)
                        content = response.content.decode(response.encoding or 'utf-8', errors='replace')
                        summarised = safe_extract_text(content)
                        description = summarised
                # Extract publication date
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = parser.parse(entry.published)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = parser.parse(entry.updated)
                else:
                    pub_date = datetime.now(timezone.utc)

                # Use entry.id if present, else fallback to link

                entry_id = self.entry_service.create_entry(
                    feed.id,
                    entry_uid,
                    entry.get("title", "No title"),
                    entry.get("link"),
                    description,
                    pub_date,
                )
        except Exception as err:
            ## SEEMS TO THROW TO HERE A LOT IN PRODUCITON BUT NOT IN DEV??
            logging.error(f"error parsing feed: {feed.feed_url}")
            logging.error(err)
            logging.error(traceback.format_exc())
            return

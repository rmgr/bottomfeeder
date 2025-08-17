from rss_parser import RSSParser
from requests import get
from sqlalchemy.orm import Session
from models.Feed import Feed
from repositories.FeedRepository import FeedRepository
from services.EntryService import EntryService
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from readabilipy import simple_json_from_html_string
import hashlib


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
    entry_service: EntryService

    def __init__(self,
                 db: Session,
                 feed_repository: FeedRepository,
                 entry_service: EntryService):
        self.db = db
        self.feed_repository = feed_repository
        self.entry_service = entry_service

    def RefreshFeeds(self):
        # TODO: Loop through feed pages
        feeds = self.feed_repository.list(self.db, 1, 100)
        for feed in feeds:
            self.RefreshFeed(feed)

    def RefreshFeed(self, feed: Feed):

        response = get(feed.feed_url)
        rss = RSSParser.parse(response.text)
        for item in rss.channel.items:
            article = simple_json_from_html_string(
                item.description.content, use_readability=True)
            description = "\n".join(t["text"] for t in article["plain_text"])
            self.entry_service.create_entry(feed.id,
                                            get_entry_uid(item, feed.feed_url),
                                            item.title.content,
                                            item.links[0].content,
                                            description,
                                            parsedate_to_datetime(item.pub_date.content) if item.pub_date is not None else datetime.now(
                                                timezone.utc),
                                            )

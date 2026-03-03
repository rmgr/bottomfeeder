from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint
import uuid

from models.Entry import Entry  # Import Entry for type hints


class FeedBase(SQLModel):
    id: uuid.UUID
    feed_name: str
    feed_url: str
    created_by: uuid.UUID
    created_date: datetime
    last_crawl_date: Optional[datetime]
    age_window: int  # seconds
    crawl_page_content: bool
    link_filter: Optional[str]
    page_filter: Optional[str]


class Feed(FeedBase, table=True):
    __tablename__ = "feeds"
    __table_args__ = (
        UniqueConstraint("feed_url", "created_by", name="uq_feed_url_created_by"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    feed_name: str = Field(nullable=False)
    feed_url: str = Field(nullable=False)
    created_by: uuid.UUID = Field(index=True, nullable=False)
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_crawl_date: Optional[datetime] = Field(default=None, nullable=True)
    age_window: int = Field(default=3 * 24)
    crawl_page_content: bool = Field(default=False)
    link_filter: Optional[str] = Field(nullable=True)
    page_filter: Optional[str] = Field(nullable=True)

    entries: List[Entry] = Relationship(back_populates="feed")


class FeedSummary(FeedBase):
    pass


class FeedCreate(SQLModel):
    feed_name: str
    feed_url: str
    created_by: uuid.UUID
    age_window: int = 7 * 24
    crawl_page_content: bool = False
    link_filter: Optional[str]
    page_filter: Optional[str]

class FeedUpdate(SQLModel):
    id: uuid.UUID
    feed_name: str
    feed_url: str
    created_by: uuid.UUID
    age_window: int = 7 * 24
    crawl_page_content: bool = False
    link_filter: Optional[str]
    page_filter: Optional[str]

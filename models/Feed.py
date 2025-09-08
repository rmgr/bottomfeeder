from typing import Optional
from datetime import datetime
from models.Entry import Entry
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint
import uuid


class FeedBase(SQLModel):
    id: uuid.UUID
    feed_name: str
    feed_url: str
    created_by: uuid.UUID
    created_date: datetime
    last_crawl_date: Optional[datetime]
    age_window: int  # seconds


class Feed(FeedBase, table=True):
    __tablename__ = "feeds"
    __table_args__ = (
        UniqueConstraint("feed_url", "created_by",
                         name="uq_feed_url_created_by"),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    feed_name: str = Field(index=False, nullable=False)
    feed_url: str = Field(index=False, nullable=False)
    created_by: uuid.UUID = Field()
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_crawl_date: Optional[datetime]
    age_window: int = 3 * 24

    entries: list["Entry"] = Relationship(back_populates="feed")


class FeedSummary(FeedBase):
    pass


class FeedCreate(SQLModel):
    feed_name: str
    feed_url: str
    created_by: uuid.UUID
    age_window: int = 3 * 24


class FeedUpdate(SQLModel):
    id: uuid.UUID 
    feed_name: str
    feed_url: str
    created_by: uuid.UUID
    age_window: int = 3 * 24

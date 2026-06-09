from typing import TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
import uuid


class EntryBase(SQLModel):
    id: str
    feed_id: uuid.UUID
    title: str
    link: str
    description: str
    publish_date: datetime
    is_read: bool


class Entry(EntryBase, table=True):
    __tablename__ = "entries"

    id: str = Field(primary_key=True)
    feed_id: uuid.UUID = Field(foreign_key="feeds.id", nullable=False)
    title: str = Field(nullable=False)
    link: str = Field(nullable=False)
    description: str = Field(nullable=False)
    publish_date: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False, nullable=False)

    feed: "Feed" = Relationship(back_populates="entries")


class EntrySummary(EntryBase):
    pass


class EntryCreate(SQLModel):
    id: str
    feed_id: uuid.UUID
    title: str
    link: str
    description: str
    publish_date: datetime
    is_read: bool


if TYPE_CHECKING:
    from models.Feed import Feed

from typing import Optional, List, Tuple
from models.Entry import Entry, EntryCreate
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session
import uuid


class EntryRepository:
    def get(self,
            entry_id: uuid.UUID,
            db: Session) -> Optional[Entry]:
        query = db.query(Entry)
        entry = query.where(Entry.id == entry_id).first()
        return entry

    # TODO: filter by user too
    def list_entries(self,
                     user_id: uuid.UUID,
                     only_unread: bool,
                     db: Session,
                     page: int = 1,
                     page_size: int = 10) -> Tuple[List[Entry], int]:
        query = db.query(Entry)
        total = query.count()
        if only_unread:
            query = query.where(Entry.is_read == False)
        feeds = query.order_by(
            desc(Entry.id)
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return (feeds, total)

    def list_by_feed(self,
                     user_id: uuid.UUID,
                     feed_id: uuid.UUID,
                     db: Session,
                     page: int = 1,
                     page_size: int = 10) -> Tuple[List[Entry], int]:
        query = db.query(Entry)
        total = query.where(Entry.feed_id == feed_id).count()
        feeds = query.order_by(
            desc(Entry.id)
        ).where(
            and_(
                Entry.feed_id == feed_id,
            )
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return (feeds, total)

    def update(self, entry: Entry, db: Session):
        db.add(entry)
        db.flush()
        db.refresh(entry)

    def create(self, feed_create: EntryCreate, db: Session) -> uuid.UUID:
        feed_data = Entry(
            **{k: v for k, v in feed_create.dict().items()})
        db.add(feed_data)
        db.flush()
        db.refresh(feed_data)
        return feed_data.id

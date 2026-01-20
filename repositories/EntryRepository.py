from typing import Optional, List, Tuple
from models.Entry import Entry, EntryCreate
from models.Feed import Feed
from sqlalchemy import desc, and_, select, exists
from sqlalchemy.orm import Session, joinedload
import uuid


class EntryRepository:
    def get(self,
            entry_id: uuid.UUID,
            db: Session) -> Optional[Entry]:
        query = db.query(Entry)
        entry = query.where(Entry.id == entry_id).first()
        return entry

    def list_all_entries(self,
                     only_unread: bool,
                     db: Session,
                     page: int = 1,
                     page_size: int = 10) -> Tuple[List[Entry], int]:
        query = db.query(Entry)
        total = query.count()
        if only_unread:
            query = query.where(Entry.is_read == False)
        entries = query.order_by(
            desc(Entry.publish_date)
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return (entries, total)


    def list_entries(self,
                     user_id: uuid.UUID,
                     only_unread: bool,
                     db: Session,
                     page: int = 1,
                     page_size: int = 10) -> Tuple[List[Entry], int]:
        query = db.query(Entry).join(Feed, Entry.feed_id == Feed.id).filter(Feed.created_by == user_id)
        if only_unread:
            query = query.filter(Entry.is_read == False)

        total = query.count()

        entries = query.options(
            joinedload(Entry.feed)
        ).order_by(
            desc(Entry.publish_date)
        ).offset(
            (page - 1) * page_size
        ).limit(
            page_size
        ).all()

        return (entries, total)

    def list_by_feed(self,
                     user_id: uuid.UUID,
                     feed_id: uuid.UUID,
                     db: Session,
                     page: int = 1,
                     page_size: int = 10) -> Tuple[List[Entry], int]:
        query = db.query(Entry).filter(Entry.feed_id == feed_id)
        total = query.count()
        entries = query.order_by(
            desc(Entry.publish_date)
        ).where(
            and_(
                Entry.feed_id == feed_id,
            )
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return (entries, total)

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

    def exists(self, entry_id: uuid.UUID, db: Session) -> bool:
        stmt = select(exists().where(Entry.id == entry_id))
        return db.scalar(stmt)

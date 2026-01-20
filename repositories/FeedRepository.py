from typing import Optional, Tuple, List
from models.Feed import Feed, FeedCreate, FeedUpdate
from models.Entry import Entry
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session
import uuid


class FeedRepository:
    def get(self,
            id: uuid.UUID,
            user_id: uuid.UUID,
            db: Session) -> Optional[Feed]:
        query = db.query(Feed)
        feed = query.where(Feed.id == id).first()
        return feed

    def list_by_user(self,
                     user_id: uuid.UUID,
                     db: Session,
                     page: int = 1,
                     page_size: int = 10) -> Tuple[List[Feed], int]:
        query = db.query(Feed).where(feed.created_by == user_id)
        total = query.count()
        feeds = query.order_by(
            desc(Feed.feed_name)
        ).where(
            Feed.created_by == user_id
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return (feeds, total)

    def list(self,
             db: Session,
             page: int = 1,
             page_size: int = 10) -> Tuple[List[Feed], int]:
        query = db.query(Feed)
        total = query.count()
        feeds = query.order_by(
            desc(Feed.feed_name)
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return (feeds, total)

    def create(self, feed_create: FeedCreate, db: Session) -> uuid.UUID:
        feed_data = Feed(
            **{k: v for k, v in feed_create.dict().items()})
        db.add(feed_data)
        db.flush()
        db.refresh(feed_data)
        return feed_data.id

    def update(self, feed_update: FeedUpdate, db: Session) -> uuid.UUID:
        feed_data = db.query(Feed).filter(Feed.id == feed_update.id).first()
        if not feed_data:
            raise HTTPException(status_code=404, detail="Feed not found")

        update_data = feed_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(feed_data, key, value)

        db.add(feed_data)  # optional, object is already in session
        db.commit()
        db.refresh(feed_data)

        return feed_data.id

    def get_existing_feeds(self, feeds: List[str], user_id: uuid.UUID, db: Session) -> List[str]: 
        feeds = db.query(Feed.feed_url).where(and_(Feed.feed_url.in_(feeds), Feed.created_by == user_id)).all()
        return [url for (url,) in feeds]  # Flatten to a list of strings

    def delete(self,
               feed_id: uuid.UUID,
               user_id: uuid.UUID,
               db: Session) -> uuid.UUID:
        # Ensure feed exists and belongs to the user
        feed = db.query(Feed).filter(
            Feed.id == feed_id,
            Feed.created_by == user_id
        ).first()

        if not feed:
            raise HTTPException(status_code=404, detail="Feed not found or not owned by user")

        # Delete related entries
        db.query(Entry).filter(Entry.feed_id == feed_id).delete()

        db.delete(feed)

        return id


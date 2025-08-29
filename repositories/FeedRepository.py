from typing import Optional, Tuple, List
from models.Feed import Feed, FeedCreate
from sqlalchemy import desc
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
        query = db.query(Feed)
        total = query.where(Feed.created_by == user_id).count()
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

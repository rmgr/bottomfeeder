from typing import Optional
from config.db import (get_db_connection)
from models.Pagination import PaginationParams, PaginatedResponse
from models.Feed import Feed, FeedCreate, FeedUpdate
from fastapi import Depends
from repositories.FeedRepository import FeedRepository
from sqlalchemy.orm import Session
import uuid
import math


class FeedService:
    db: Session
    feed_repository: FeedRepository

    def __init__(self,
                 db: Session = Depends(get_db_connection),
                 feed_repository: FeedRepository = Depends()):
        self.db = db
        self.feed_repository = feed_repository

    def ListFeeds(self,
                  user_id: uuid,
                  pagination: PaginationParams) -> PaginatedResponse:
        feeds, total = self.feed_repository.list_by_user(
            user_id=user_id,
            db=self.db,
            page=pagination.page,
            page_size=pagination.page_size
        )

        total_pages = math.ceil(total / pagination.page_size)

        return PaginatedResponse(
            items=feeds,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )

    def get(self,
            feed_id: uuid,
            user_id: uuid) -> Optional[Feed]:

        feed = self.feed_repository.get(
            id=feed_id,
            user_id=user_id,
            db=self.db,
        )

        return feed

    def update_feed(self,
                    feed_id: uuid.UUID,
                    feed_name: str,
                    feed_url: str,
                    created_by: uuid.UUID,
                    age_window: int,
                    crawl_page_content: bool) -> uuid.UUID:
        feed_update = FeedUpdate(id=feed_id,
                                 feed_name=feed_name,
                                 feed_url=feed_url,
                                 created_by=created_by,
                                 age_window=age_window,
                                 crawl_page_content=crawl_page_content)
        id = self.feed_repository.update(feed_update, self.db)
        self.db.commit()
        return id
    
    def create_feed(self,
                    feed_name: str,
                    feed_url: str,
                    created_by: uuid.UUID,
                    age_window: int) -> uuid.UUID:
        feed_create = FeedCreate(feed_name=feed_name,
                                 feed_url=feed_url,
                                 created_by=created_by,
                                 age_window=age_window)
        id = self.feed_repository.create(feed_create, self.db)
        self.db.commit()
        return id

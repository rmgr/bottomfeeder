from config.db import (get_db_connection)
from models.Pagination import PaginationParams, PaginatedResponse
from models.Feed import FeedCreate
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

    def create_feed(self,
                    feed_name: str,
                    feed_url: str,
                    created_by: uuid.UUID,
                    crawl_interval: int,
                    age_window: int) -> uuid.UUID:
        feed_create = FeedCreate(feed_name=feed_name,
                                 feed_url=feed_url,
                                 created_by=created_by,
                                 crawl_interval=crawl_interval,
                                 age_window=age_window)
        id = self.feed_repository.create(feed_create, self.db)
        self.db.commit()
        return id

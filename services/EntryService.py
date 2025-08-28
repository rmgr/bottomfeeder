from config.db import (get_db_connection)
from models.Pagination import PaginationParams, PaginatedResponse
from models.Entry import EntryCreate
from fastapi import Depends
from datetime import datetime
from repositories.EntryRepository import EntryRepository
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
import math


class EntryService:
    db: Session
    entry_repository: EntryRepository

    def __init__(self,
                 db: Session = Depends(get_db_connection),
                 entry_repository: EntryRepository = Depends()):
        self.db = db
        self.entry_repository = entry_repository

    def get_entry(self,
                  entry_id: uuid.UUID) -> PaginatedResponse:
        entry = self.entry_repository.get(
            entry_id,
            self.db,
        )
        return entry

    def ListUnreadEntries(self,
                          user_id: uuid,
                          pagination: PaginationParams) -> PaginatedResponse:
        entries, total = self.entry_repository.list_entries(
            user_id,
            True,
            self.db,
            page=pagination.page,
            page_size=pagination.page_size
        )

        total_pages = math.ceil(total / pagination.page_size)

        return PaginatedResponse(
            items=entries,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )

    def ListEntries(self,
                    user_id: uuid,
                    pagination: PaginationParams) -> PaginatedResponse:
        entries, total = self.entry_repository.list_entries(
            user_id,
            self.db,
            page=pagination.page,
            page_size=pagination.page_size
        )

        total_pages = math.ceil(total / pagination.page_size)

        return PaginatedResponse(
            items=entries,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )

    def ListEntriesForFeed(self,
                           feed_id: uuid,
                           user_id: uuid,
                           pagination: PaginationParams) -> PaginatedResponse:
        entries, total = self.entry_repository.list_by_feed(
            user_id,
            feed_id,
            self.db,
            page=pagination.page,
            page_size=pagination.page_size
        )

        total_pages = math.ceil(total / pagination.page_size)

        return PaginatedResponse(
            items=entries,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )

    def mark_unread(self,
                    entry_id: str):
        entry = self.entry_repository.get(entry_id, self.db)
        entry.is_read = False
        self.entry_repository.update(entry, self.db)
        self.db.commit()

    def mark_read(self,
                  entry_id: str):
        entry = self.entry_repository.get(entry_id, self.db)
        entry.is_read = True
        self.entry_repository.update(entry, self.db)
        self.db.commit()

    def create_entry(self,
                     feed_id: uuid.UUID,
                     entry_id: str,
                     title: str,
                     link: str,
                     description: str,
                     publish_date: datetime) -> uuid.UUID:
        try:
            entry_create = EntryCreate(feed_id=feed_id,
                                       id=entry_id,
                                       title=title,
                                       link=link,
                                       description=description,
                                       publish_date=publish_date,
                                       is_read=False
                                       )
            self.entry_repository.create(entry_create, self.db)
            self.db.commit()
            return entry_id

        except IntegrityError:
            self.db.rollback()

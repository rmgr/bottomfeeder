from pydantic import BaseModel
from datetime import datetime
import uuid


class CreateEntryRequest(BaseModel):
    feed_id: uuid.UUID
    title: str
    link: str
    description: str
    publish_date: datetime
    is_read: bool

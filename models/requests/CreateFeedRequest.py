from pydantic import BaseModel
from typing import Optional


class CreateFeedRequest(BaseModel):
    feed_name: str
    feed_url: str
    crawl_interval: Optional[int]
    age_window: Optional[int]

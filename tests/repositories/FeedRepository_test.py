import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.Feed import Feed, FeedBase
from repositories.FeedRepository import FeedRepository


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    FeedBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def repo():
    return FeedRepository()


def _make_feed(user_id, *, feed_name, created_date, latest_entry_date=None):
    return Feed(
        id=uuid.uuid4(),
        feed_name=feed_name,
        feed_url=f"https://example.com/{feed_name}",
        created_by=user_id,
        created_date=created_date,
        latest_entry_date=latest_entry_date,
    )

def test_list_by_user_orders_by_effective_date_desc(db, repo):
    user_id = uuid.uuid4()
    base_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    oldest = _make_feed(user_id, feed_name="oldest",
                        created_date=base_date)
    newest = _make_feed(user_id, feed_name="newest",
                        created_date=base_date + timedelta(days=1),
                        latest_entry_date=base_date + timedelta(days=10))
    middle = _make_feed(user_id, feed_name="middle",
                        created_date=base_date + timedelta(days=-12), ## Oldest, overridden by latest_entry_date
                        latest_entry_date=base_date + timedelta(days=5)) 

    db.add_all([oldest, newest, middle])
    db.flush()

    feeds, total = repo.list_by_user(user_id, db)

    assert total == 3
    assert [f.feed_name for f in feeds] == ["newest", "middle", "oldest"]

def test_list_by_user_falls_back_to_created_date_when_no_entry_date(db, repo):
    user_id = uuid.uuid4()
    base_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    no_entries = _make_feed(user_id, feed_name="no_entries",
                            created_date=base_date + timedelta(days=20))
    has_entries = _make_feed(user_id, feed_name="has_entries",
                             created_date=base_date,
                             latest_entry_date=base_date + timedelta(days=5))

    db.add_all([no_entries, has_entries])
    db.flush()

    feeds, _ = repo.list_by_user(user_id, db)

    assert [f.feed_name for f in feeds] == ["no_entries", "has_entries"]

def test_list_by_user_breaks_ties_by_id_desc(db, repo):
    user_id = uuid.uuid4()
    same_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    low_id = Feed(id=uuid.UUID(int=1), feed_name="low",
                  feed_url="https://example.com/low", created_by=user_id,
                  created_date=same_date)
    high_id = Feed(id=uuid.UUID(int=100), feed_name="high",
                   feed_url="https://example.com/high", created_by=user_id,
                   created_date=same_date)

    db.add_all([low_id, high_id])
    db.flush()

    feeds, _ = repo.list_by_user(user_id, db)

    assert [f.feed_name for f in feeds] == ["high", "low"]

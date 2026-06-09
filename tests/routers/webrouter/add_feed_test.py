import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from services.FeedService import FeedService
from services.AccountService import try_get_current_user
from models.Account import AccountSummary
import uuid
from datetime import datetime

MOCK_USER_ID = uuid.uuid4()
MOCK_FEED_ID = uuid.uuid4()

MOCK_USER = AccountSummary(
    id=MOCK_USER_ID,
    account_name="Test User",
    email_address="test@example.com",
    is_active=1,
    date_created=datetime.now(),
    date_updated=datetime.now()
)


def make_mock_feed_service():
    mock = MagicMock(spec=FeedService)
    mock.create_feed.return_value = MOCK_FEED_ID
    return mock


@pytest.fixture
def mock_feed_service():
    return make_mock_feed_service()


@pytest.fixture
def authenticated_client(mock_feed_service):
    app.dependency_overrides[try_get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[FeedService] = lambda: mock_feed_service
    client = TestClient(app, raise_server_exceptions=False)
    yield client, mock_feed_service
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    app.dependency_overrides[try_get_current_user] = lambda: None
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


VALID_FEED_DATA = {
    "feed_name": "My Feed",
    "feed_url": "https://example.com/feed.xml",
}


class TestAddFeed:
    # Regression tests: optional filter fields
    @pytest.mark.parametrize("data", [
        {"feed_name": "My Feed", "feed_url": "https://example.com/feed.xml"},
        {"feed_name": "My Feed", "feed_url": "https://example.com/feed.xml", "link_filter": ".*sponsored.*"},
        {"feed_name": "My Feed", "feed_url": "https://example.com/feed.xml", "page_filter": ".*ad.*"},
    ])
    def test_add_feed_succeeds_without_filters(self, authenticated_client, data):
        client, _ = authenticated_client
        result = client.post("/add-feed", data=data, follow_redirects=False)
        assert result.status_code == 303


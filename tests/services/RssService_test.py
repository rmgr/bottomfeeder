from services import RssService
from datetime import datetime, timezone
import pytest

# content of test_class.py
class TestRssService:
    def test_safe_extract_text_returns_empty_string_when_trafilatura_returns_none(self):
        html = ""
        result = RssService.safe_extract_text(html)
        assert result == ""

    @pytest.mark.parametrize("input,expected", [
        ("Mon, 09 Jun 2026 00:00:00 GMT",    "2026-06-09T00:00:00+00:00"),
        ("2026-06-09T14:30:00+00:00",        "2026-06-09T14:30:00+00:00"),
        ("2026-06-10T00:00:00+09:30",        "2026-06-09T14:30:00+00:00"),
        ("not-a-date",                       "not-a-date"),
        ("",                                 ""),
        (None,                               ""),
    ])
    def test_normalise_date(self, input, expected):
        result = RssService.normalise_date(input)
        assert result == expected

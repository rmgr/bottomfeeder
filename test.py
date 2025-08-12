from rss_parser import RSSParser
from requests import get
from datetime import datetime
from email.utils import parsedate_to_datetime

response = get("https://eli.li/feed.rss")
rss = RSSParser.parse(response.text)
for item in rss.channel.items:
    print(item.links[0].content)
    print(item.title.content)
    print(parsedate_to_datetime(item.pub_date.content).year)
    print(item.description.content)

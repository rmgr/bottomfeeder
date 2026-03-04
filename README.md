# Bottomfeeder

An RSS feed reader just for me

## Features

- Set expiry dates on feed items
- Filter feed items and urls by regex

## Requirements

- Python 3.12+
- Dependencies listed in `pyproject.toml`

## Installation

 I personally run it using docker. Configuration can be done with the .env file 

```bash
docker build -t bottomfeeder:latest .
docker run \
  -e DATABASE_URL=sqlite:///data.db \
  -e LOG_LEVEL=DEBUG \
  -e REFRESH_INTERVAL=30 \
  -e STALE_INTERVAL=30 \
  -p 8000:8000
  bottomfeeder:latest
```

## License

[AGPL version 3](LICENSE)

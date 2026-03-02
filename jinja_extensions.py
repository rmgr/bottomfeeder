import re
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

_original_striptags = templates.env.filters["striptags"]

def striptags_spaced(value: str) -> str:
    value = re.sub(r'</(p|div|li|h[1-6])>', ' ', value, flags=re.IGNORECASE)
    value = re.sub(r'<br\s*/?>', ' ', value, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', _original_striptags(value)).strip()

templates.env.filters["striptags"] = striptags_spaced

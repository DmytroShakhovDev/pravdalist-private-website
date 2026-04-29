"""Server-side rendered page routes."""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.i18n.loader import available_languages, load_page, t as _t

logger = logging.getLogger(__name__)
router = APIRouter()

templates = Jinja2Templates(directory=str(__import__("pathlib").Path(__file__).parent.parent / "templates"))


def _detect_lang(request: Request, default: str = "ua") -> str:
    """Detect language from query -> cookie -> Accept-Language -> default."""
    supported = available_languages()
    lang = request.query_params.get("lang")
    if lang in supported:
        return lang
    lang = request.cookies.get("lang")
    if lang in supported:
        return lang
    accept = request.headers.get("accept-language", "")
    for part in accept.split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code == "uk":
            code = "ua"
        if code in supported:
            return code
    return default


def _ctx(request: Request, page: str) -> Dict[str, Any]:
    lang = _detect_lang(request)
    strings = load_page(page, lang)

    def t(key: str, **fmt: Any) -> str:
        return _t(strings, key, **fmt)

    tiles_list = []
    tiles_node = strings.get("tiles", {})
    for key in sorted(tiles_node.keys()):
        tile = tiles_node[key]
        if isinstance(tile, dict):
            tiles_list.append({"key": key, "title": tile.get("title", ""), "desc": tile.get("desc", "")})

    return {
        "lang": lang,
        "t": t,
        "strings": strings,
        "available_languages": available_languages(),
        "tiles_data": tiles_list,
    }


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    ctx = _ctx(request, "home")
    return templates.TemplateResponse(request, "pages/home.html", ctx)


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request) -> HTMLResponse:
    ctx = _ctx(request, "about")
    return templates.TemplateResponse(request, "pages/about.html", ctx)


@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request) -> HTMLResponse:
    ctx = _ctx(request, "contacts")
    return templates.TemplateResponse(request, "pages/contacts.html", ctx)

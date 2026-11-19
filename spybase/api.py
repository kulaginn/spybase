"""REST API SpyBase (Рязанцев Д., компонент «REST API»; обработка ошибок — Саргсян Л.).

Запуск:  uvicorn spybase.api:app --reload    → http://127.0.0.1:8000  (интерфейс)  и /docs (Swagger)
Интерфейс обращается к данным только через это API, к базе напрямую не ходит.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import db, repository
from .errors import ApiError, not_found, validate_login, validate_search

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("SPYBASE_DB", str(ROOT / "spybase.db"))

app = FastAPI(title="SpyBase API", version="0.1.0")
con = db.connect(DB_PATH)


@app.exception_handler(ApiError)
async def api_error(_: Request, ex: ApiError) -> JSONResponse:
    return JSONResponse(ex.body(), status_code=ex.status)


@app.exception_handler(Exception)
async def unexpected(_: Request, ex: Exception) -> JSONResponse:      # E-500: не показываем детали наружу
    return JSONResponse({"error": {"code": "E-500", "message": "Внутренняя ошибка сервера"}}, status_code=500)


@app.get("/api/ads")
def search_ads(q: str = "", country: str = "", niche: str = "", min_days: int = 0, sort: str = "last_seen",
               limit: int = 20, offset: int = 0) -> dict:
    validate_search(q, country, niche, min_days, sort, limit, offset, set(db.NICHES))
    return repository.search(con, repository.AdFilter(q.strip(), country, niche, min_days, sort, limit, offset))


@app.get("/api/ads/{ad_id}")
def ad_card(ad_id: int) -> dict:
    ad = repository.get_ad(con, ad_id)
    if not ad:
        raise not_found("Объявление", ad_id)
    return ad


@app.get("/api/niches")
def niches() -> dict:
    return db.NICHES


@app.get("/api/stats")
def stats() -> dict:
    return repository.stats(con)


@app.get("/api/favorites")
def list_favorites(x_user: str = Header(default="")) -> list:
    return repository.favorites(con, validate_login(x_user))


@app.post("/api/favorites/{ad_id}")
def add_favorite(ad_id: int, x_user: str = Header(default="")) -> dict:
    login = validate_login(x_user)
    if not repository.get_ad(con, ad_id):
        raise not_found("Объявление", ad_id)
    added = repository.add_favorite(con, login, ad_id)
    return {"ok": True, "added": added}


@app.delete("/api/favorites/{ad_id}")
def remove_favorite(ad_id: int, x_user: str = Header(default="")) -> dict:
    if not repository.remove_favorite(con, validate_login(x_user), ad_id):
        raise not_found("В избранном объявление", ad_id)
    return {"ok": True}


WEB = ROOT / "web"
if WEB.is_dir():
    app.mount("/static", StaticFiles(directory=WEB), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB / "index.html")

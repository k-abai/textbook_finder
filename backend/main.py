from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


logger = logging.getLogger("textbook_finder")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

APP_ENV = os.getenv("APP_ENV", "development").lower()
LIBRARY_PATH = Path(os.getenv("LIBRARY_PATH", "./library")).resolve()
LIBRARY_PATH.mkdir(parents=True, exist_ok=True)


def _cors_origins() -> list[str]:
    if APP_ENV in {"prod", "production"}:
        origins = os.getenv("CORS_ORIGINS", "")
        if origins:
            return [origin.strip() for origin in origins.split(",") if origin.strip()]
        return ["https://example.com"]
    return ["*"]


app = FastAPI(title="TextbookFinder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address, default_limits=[])
app.state.limiter = limiter


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResult(BaseModel):
    source_id: str
    title: str
    author: str
    score: float


class DownloadRequest(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=300)
    author: str = Field(default="Unknown", max_length=200)


class DownloadConfirmRequest(BaseModel):
    download_id: str = Field(..., min_length=1)


class ErrorPayload(BaseModel):
    ok: bool = False
    error: dict[str, Any]


_pending_downloads: dict[str, dict[str, Any]] = {}


def _error_response(
    *,
    code: str,
    message: str,
    details: Any | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


def _book_path(book_id: str) -> Path:
    return LIBRARY_PATH / f"{book_id}.json"


def _resolve_and_validate(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(LIBRARY_PATH)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Path is outside library") from exc
    return resolved


def _load_book(book_id: str) -> dict[str, Any]:
    metadata_path = _resolve_and_validate(_book_path(book_id))
    if not metadata_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    with metadata_path.open("r", encoding="utf-8") as f:
        book = json.load(f)

    return book


def _list_books() -> list[dict[str, Any]]:
    books: list[dict[str, Any]] = []
    for meta_file in LIBRARY_PATH.glob("*.json"):
        with meta_file.open("r", encoding="utf-8") as f:
            books.append(json.load(f))
    books.sort(key=lambda b: b.get("created_at", ""), reverse=True)
    return books


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    retry_after = "60"
    reset_at = getattr(exc, "reset_at", None)
    if isinstance(reset_at, (int, float)):
        retry_after = str(max(1, int(reset_at - time.time())))

    logger.warning(
        "RATE_LIMIT_HIT path=%s ip=%s detail=%s",
        request.url.path,
        get_remote_address(request),
        str(exc.detail),
    )

    # Keep slowapi's header behavior available on top of our JSON shape.
    base_response = _rate_limit_exceeded_handler(request, exc)
    headers = dict(base_response.headers)
    headers["Retry-After"] = headers.get("Retry-After", retry_after)

    return _error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests",
        details={"limit": str(exc.detail)},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers=headers,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return _error_response(
        code="HTTP_ERROR",
        message=str(exc.detail),
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details=exc.errors(),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error", exc_info=exc)
    return _error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "TextbookFinder API",
        "environment": APP_ENV,
        "library_path": str(LIBRARY_PATH),
    }


@app.post("/search")
@limiter.limit("10/minute")
async def search(request: Request, payload: SearchRequest) -> dict[str, Any]:
    _ = request
    normalized = payload.query.strip()
    results = [
        SearchResult(
            source_id=f"src-{idx}-{normalized.lower().replace(' ', '-')}",
            title=f"{normalized} - Edition {idx}",
            author="Sample Author",
            score=max(0.0, 1 - (idx * 0.05)),
        ).model_dump()
        for idx in range(1, payload.limit + 1)
    ]
    return {"ok": True, "query": normalized, "results": results}


@app.post("/download")
@limiter.limit("5/minute")
async def download(request: Request, payload: DownloadRequest) -> dict[str, Any]:
    _ = request
    download_id = str(uuid.uuid4())
    _pending_downloads[download_id] = {
        "source_id": payload.source_id,
        "title": payload.title,
        "author": payload.author,
        "created_at": int(time.time()),
    }
    return {
        "ok": True,
        "download_id": download_id,
        "status": "pending_confirmation",
    }


@app.post("/download/confirm")
@limiter.limit("5/minute")
async def download_confirm(request: Request, payload: DownloadConfirmRequest) -> dict[str, Any]:
    _ = request
    record = _pending_downloads.pop(payload.download_id, None)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download request not found or expired")

    book_id = str(uuid.uuid4())
    file_path = _resolve_and_validate(LIBRARY_PATH / f"{book_id}.txt")
    metadata_path = _resolve_and_validate(_book_path(book_id))

    file_contents = (
        f"Title: {record['title']}\n"
        f"Author: {record['author']}\n"
        f"Source: {record['source_id']}\n"
        "\nThis is a placeholder downloaded textbook file.\n"
    )
    with file_path.open("w", encoding="utf-8") as f:
        f.write(file_contents)

    metadata = {
        "id": book_id,
        "title": record["title"],
        "author": record["author"],
        "source_id": record["source_id"],
        "file_path": str(file_path),
        "created_at": int(time.time()),
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {"ok": True, "status": "downloaded", "book": metadata}


@app.get("/library")
async def library() -> dict[str, Any]:
    return {"ok": True, "items": _list_books()}


@app.get("/library/search")
async def library_search(q: str = "") -> dict[str, Any]:
    query = q.strip().lower()
    items = _list_books()
    if query:
        items = [
            item
            for item in items
            if query in item.get("title", "").lower() or query in item.get("author", "").lower()
        ]
    return {"ok": True, "query": q, "items": items}


@app.get("/library/{book_id}")
async def library_book(book_id: str) -> dict[str, Any]:
    return {"ok": True, "book": _load_book(book_id)}


@app.delete("/library/{book_id}")
async def library_delete(book_id: str) -> dict[str, Any]:
    book = _load_book(book_id)
    file_path = _resolve_and_validate(Path(book["file_path"]))
    meta_path = _resolve_and_validate(_book_path(book_id))

    if file_path.exists():
        file_path.unlink()
    if meta_path.exists():
        meta_path.unlink()

    return {"ok": True, "deleted": book_id}


@app.post("/library/{book_id}/delete")
async def library_delete_variant(book_id: str) -> dict[str, Any]:
    return await library_delete(book_id)


@app.get("/library/{book_id}/open")
async def library_open(book_id: str) -> FileResponse:
    book = _load_book(book_id)
    file_path = _resolve_and_validate(Path(book["file_path"]))
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book file not found")
    return FileResponse(path=file_path, filename=file_path.name, media_type="text/plain")


@app.post("/library/{book_id}/open")
async def library_open_variant(book_id: str) -> FileResponse:
    return await library_open(book_id)

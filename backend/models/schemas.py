from __future__ import annotations

import re
from typing import Literal
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, Field, field_validator


_BLACKLIST_PATTERNS = [
    re.compile(r"\.{2}"),
    re.compile(r"%2e", re.IGNORECASE),
    re.compile(r"%2f", re.IGNORECASE),
    re.compile(r"%5c", re.IGNORECASE),
    re.compile(r"[\n\r\t]"),
    re.compile(r"[;&|`$<>]"),
]


def sanitize_string(value: str) -> str:
    """Sanitize untrusted string input.

    Pipeline:
    1. trim
    2. remove null bytes
    3. strip shell metacharacters/newlines/tabs
    4. strip traversal encodings/sequences
    5. truncate to 500
    6. raise ValueError if blacklisted patterns remain
    """
    sanitized = value.strip()
    sanitized = sanitized.replace("\x00", "")

    # Strip shell metacharacters and control whitespace.
    sanitized = re.sub(r"[;&|`$<>\n\r\t]", "", sanitized)

    # Strip traversal encodings/sequences.
    sanitized = re.sub(r"\.\.", "", sanitized)
    sanitized = re.sub(r"(?i)%2e", "", sanitized)
    sanitized = re.sub(r"(?i)%2f", "", sanitized)
    sanitized = re.sub(r"(?i)%5c", "", sanitized)

    # Normalize any encoded traversal remnants after decoding once.
    decoded = unquote(sanitized)
    decoded = re.sub(r"\.\.", "", decoded)
    decoded = re.sub(r"[\\/]", "", decoded)
    sanitized = decoded[:500]

    if any(pattern.search(sanitized) for pattern in _BLACKLIST_PATTERNS):
        raise ValueError("Invalid characters in input")

    return sanitized


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    file_type: Literal["pdf", "epub", "mobi", "any"] = "any"
    sort_by: Literal["relevance", "newest", "oldest"] = "relevance"
    max_results: int = Field(default=20, ge=1, le=100)

    @field_validator("query", "file_type", "sort_by", mode="before")
    @classmethod
    def _sanitize_strings(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Expected a string value")
        return sanitize_string(value)


class RawResult(BaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    url: str
    source: str
    file_type: Literal["pdf", "epub", "mobi", "unknown"] = "unknown"
    year: int | None = None
    language: str | None = None
    isbn: str | None = None
    size: str | None = None


class ScoredResult(RawResult):
    score: float = Field(ge=0.0)
    score_reason: str | None = None


class DownloadRequest(BaseModel):
    url: str
    title: str | None = None
    source: str | None = None

    @field_validator("url", "title", "source", mode="before")
    @classmethod
    def _sanitize_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Expected a string value")
        return sanitize_string(value)

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        lowered = value.lower().strip()

        if lowered.startswith("javascript:"):
            raise ValueError("URL scheme 'javascript:' is not allowed")
        if lowered.startswith("data:"):
            raise ValueError("URL scheme 'data:' is not allowed")
        if lowered.startswith("ftp:"):
            raise ValueError("URL scheme 'ftp:' is not allowed")

        if not lowered.startswith("https://"):
            raise ValueError("URL must start with 'https://'")

        parsed = urlparse(value)
        host = parsed.hostname
        if not host:
            raise ValueError("URL must include a valid host")

        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host) or ":" in host:
            raise ValueError("IP-host URLs are not allowed")

        return value


class DownloadResponse(BaseModel):
    success: bool
    message: str
    file_path: str | None = None
    filename: str | None = None
    file_size_bytes: int | None = None
    sha256: str | None = None


class URLScanResult(BaseModel):
    url: str
    status: Literal["clean", "suspicious", "blocked"]
    is_safe: bool
    reasons: list[str] = Field(default_factory=list)


class FileValidationResult(BaseModel):
    is_valid: bool
    mime_type: str | None = None
    extension: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    errors: list[str] = Field(default_factory=list)


class BookRecord(BaseModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    source: str
    url: str
    file_type: Literal["pdf", "epub", "mobi", "unknown"] = "unknown"
    year: int | None = None
    isbn: str | None = None
    score: float | None = None
    local_path: str | None = None
    downloaded_at: str | None = None

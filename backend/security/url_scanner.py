from __future__ import annotations

import http.client
import ipaddress
import socket
from dataclasses import dataclass
from typing import Iterable, Sequence
from urllib.parse import urljoin, urlparse


class URLValidationError(ValueError):
    """Raised when a URL fails SSRF safety validation."""


@dataclass(frozen=True)
class ResolvedTarget:
    hostname: str
    addresses: tuple[ipaddress._BaseAddress, ...]


@dataclass(frozen=True)
class HTTPResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes


class URLScanner:
    """SSRF-focused URL validator and fetch helper."""

    def __init__(self, *, timeout: float = 10.0, max_redirects: int = 5) -> None:
        self.timeout = timeout
        self.max_redirects = max_redirects

    def scan(self, url: str) -> ResolvedTarget:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise URLValidationError("Only HTTP and HTTPS URLs are allowed")
        if not parsed.hostname:
            raise URLValidationError("URL must include a hostname")

        addresses = self.resolve_and_validate_hostname(parsed.hostname)
        return ResolvedTarget(hostname=parsed.hostname, addresses=addresses)

    def resolve_and_validate_hostname(self, hostname: str) -> tuple[ipaddress._BaseAddress, ...]:
        self._validate_hostname(hostname)
        addresses = self._resolve_hostname(hostname)
        self._reject_disallowed_addresses(addresses)
        return addresses

    def safe_request(self, method: str, url: str, headers: dict[str, str] | None = None) -> HTTPResponse:
        """Perform request with per-hop redirect revalidation."""
        current_url = url
        for _ in range(self.max_redirects + 1):
            self.scan(current_url)
            response = self._send_request(method, current_url, headers=headers or {})

            if not self._is_redirect(response.status_code):
                return response

            location = response.headers.get("Location") or response.headers.get("location")
            if not location:
                raise URLValidationError("Redirect response missing Location header")
            next_url = urljoin(current_url, location)
            self.scan(next_url)
            current_url = next_url

        raise URLValidationError("Too many redirects")

    def _send_request(self, method: str, url: str, headers: dict[str, str]) -> HTTPResponse:
        parsed = urlparse(url)
        conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        connection = conn_cls(parsed.hostname, parsed.port, timeout=self.timeout)

        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        connection.request(method.upper(), path, headers=headers)
        raw_response = connection.getresponse()
        body = raw_response.read()
        response_headers = {k: v for k, v in raw_response.getheaders()}
        connection.close()
        return HTTPResponse(status_code=raw_response.status, headers=response_headers, body=body)

    @staticmethod
    def _is_redirect(status_code: int) -> bool:
        return status_code in {301, 302, 303, 307, 308}

    @staticmethod
    def _validate_hostname(hostname: str) -> None:
        normalized = hostname.rstrip(".").lower()

        if normalized == "localhost":
            raise URLValidationError("localhost is not allowed")
        if normalized.endswith(".local"):
            raise URLValidationError(".local hostnames are not allowed")
        if "." not in normalized:
            raise URLValidationError("Single-label hostnames are not allowed")

        labels = normalized.split(".")
        if any(not label for label in labels):
            raise URLValidationError("Hostname labels cannot be empty")

        suffix = labels[-1]
        if suffix.isdigit() or len(suffix) < 2 or not suffix.replace("-", "").isalnum():
            raise URLValidationError("Hostname must include a valid public suffix")

    @staticmethod
    def _resolve_hostname(hostname: str) -> tuple[ipaddress._BaseAddress, ...]:
        try:
            addr_info = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise URLValidationError(f"Failed to resolve hostname: {hostname}") from exc

        addresses: list[ipaddress._BaseAddress] = []
        for _, _, _, _, sockaddr in addr_info:
            raw_ip = sockaddr[0]
            ip_obj = ipaddress.ip_address(raw_ip)
            if ip_obj not in addresses:
                addresses.append(ip_obj)

        if not addresses:
            raise URLValidationError("Hostname did not resolve to any IP addresses")
        return tuple(addresses)

    @staticmethod
    def _reject_disallowed_addresses(addresses: Sequence[ipaddress._BaseAddress]) -> None:
        blocked = [str(ip) for ip in addresses if URLScanner._is_disallowed_ip(ip)]
        if blocked:
            raise URLValidationError(f"Resolved IPs are not publicly routable: {', '.join(blocked)}")

    @staticmethod
    def _is_disallowed_ip(ip_obj: ipaddress._BaseAddress) -> bool:
        checks = (
            ip_obj.is_loopback,
            ip_obj.is_link_local,
            ip_obj.is_private,
            ip_obj.is_multicast,
            ip_obj.is_reserved,
            ip_obj.is_unspecified,
            not ip_obj.is_global,
        )
        if isinstance(ip_obj, ipaddress.IPv6Address):
            checks = checks + (ip_obj.is_site_local,)
        return any(checks)

    @staticmethod
    def classify_addresses(addresses: Iterable[ipaddress._BaseAddress]) -> frozenset[str]:
        classes = set()
        for ip_obj in addresses:
            classes.add("disallowed" if URLScanner._is_disallowed_ip(ip_obj) else "public")
        return frozenset(classes)

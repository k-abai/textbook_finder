from __future__ import annotations

import ipaddress
import socket

import pytest

from backend.security.url_scanner import URLScanner, URLValidationError


def _addrinfo(ip: str, family: int = socket.AF_INET):
    return [(family, socket.SOCK_STREAM, 6, "", (ip, 0))]


def test_rejects_private_ip_resolution(monkeypatch):
    scanner = URLScanner()

    def fake_getaddrinfo(host, *_args, **_kwargs):
        assert host == "example.com"
        return _addrinfo("10.0.0.8")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(URLValidationError, match="not publicly routable"):
        scanner.scan("https://example.com/resource")


def test_redirect_revalidation_blocks_ssrf_hop(monkeypatch):
    scanner = URLScanner(max_redirects=3)

    def fake_getaddrinfo(host, *_args, **_kwargs):
        if host == "public.example":
            return _addrinfo("93.184.216.34")
        if host == "internal.example":
            return _addrinfo("127.0.0.1")
        raise AssertionError(f"Unexpected host lookup: {host}")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    class FakeResponse:
        def __init__(self, status_code: int, location: str | None = None):
            self.status_code = status_code
            self.headers = {}
            self.body = b""
            if location is not None:
                self.headers["Location"] = location

    def fake_send_request(method, url, headers):
        assert method == "GET"
        if url == "https://public.example/start":
            return FakeResponse(302, "https://internal.example/secret")
        raise AssertionError(f"Unexpected request URL: {url}")

    monkeypatch.setattr(scanner, "_send_request", fake_send_request)

    with pytest.raises(URLValidationError, match="not publicly routable"):
        scanner.safe_request("GET", "https://public.example/start")


def test_rejects_localhost_local_and_single_label_names(monkeypatch):
    scanner = URLScanner()

    # Ensure these rejections happen before DNS resolution.
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: _addrinfo("93.184.216.34"))

    for url in (
        "https://localhost/path",
        "https://printer.local/path",
        "https://intranet/path",
    ):
        with pytest.raises(URLValidationError):
            scanner.scan(url)


def test_allows_public_ipv4_and_ipv6(monkeypatch):
    scanner = URLScanner()

    def fake_getaddrinfo(host, *_args, **_kwargs):
        assert host == "example.com"
        return _addrinfo("93.184.216.34") + _addrinfo("2606:2800:220:1:248:1893:25c8:1946", socket.AF_INET6)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    target = scanner.scan("https://example.com/")
    assert ipaddress.ip_address("93.184.216.34") in target.addresses
    assert ipaddress.ip_address("2606:2800:220:1:248:1893:25c8:1946") in target.addresses

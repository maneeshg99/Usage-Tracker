"""HTTP client that impersonates a real browser's TLS fingerprint.

claude.ai and chatgpt.com use Cloudflare which detects Python's `requests`
library via TLS fingerprinting and returns 403. `curl_cffi` impersonates a
real browser's TLS handshake to bypass this.
"""

from __future__ import annotations

from curl_cffi import requests as cffi_requests


def get(url: str, *, headers: dict, timeout: int = 15) -> HTTPResponse:
    """GET request impersonating Chrome."""
    resp = cffi_requests.get(
        url,
        headers=headers,
        timeout=timeout,
        impersonate="chrome",
    )
    return HTTPResponse(resp)


def post(url: str, *, headers: dict, json: dict | None = None, timeout: int = 15) -> HTTPResponse:
    """POST request impersonating Chrome."""
    resp = cffi_requests.post(
        url,
        headers=headers,
        json=json,
        timeout=timeout,
        impersonate="chrome",
    )
    return HTTPResponse(resp)


class HTTPResponse:
    """Thin wrapper that provides the same interface as requests.Response."""

    def __init__(self, resp):
        self._resp = resp
        self.status_code = resp.status_code
        self.headers = resp.headers

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(
                f"{self.status_code} Error: {self._resp.reason or 'Unknown'} "
                f"for url: {self._resp.url}"
            )

    def json(self):
        return self._resp.json()

    @property
    def text(self):
        return self._resp.text

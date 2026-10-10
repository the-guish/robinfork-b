# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: an API answer, a stream, a refusal, a
redirect and the files of the interface alike. A browser shows none of them, so the UI cannot
assert them."""

from __future__ import annotations

import uuid

import httpx
import pytest

from util.controller_db import requires_postgres

pytestmark = requires_postgres

SECURITY_HEADERS = {
    "content-security-policy": (
        "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        " img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none';"
        " form-action 'none'; frame-ancestors 'none'"
    ),
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "referrer-policy": "same-origin",
}


def assert_secured(response: httpx.Response) -> None:
    carried = {name: response.headers.get(name) for name in SECURITY_HEADERS}
    assert carried == SECURITY_HEADERS, (response.request.url, response.status_code)


@pytest.mark.parametrize(
    ("method", "path", "headers", "status"),
    [
        ("GET", "/health", {}, 200),
        ("GET", "/api/conversations", {}, 200),
        ("GET", "/", {}, 307),
        ("GET", "/ui/", {}, 200),
        ("GET", "/ui/index.html", {}, 200),
        ("GET", "/ui/no-such-file.js", {}, 404),
        ("GET", f"/api/conversations/{uuid.UUID(int=0)}", {}, 404),
        ("GET", "/api/no-such-route", {}, 404),
        ("DELETE", "/health", {}, 405),
        ("POST", "/api/turns", {}, 422),
        ("POST", "/api/turns", {"origin": "https://elsewhere.example"}, 403),
        ("GET", "/api/conversations", {"host": "elsewhere.example"}, 403),
        ("GET", "/ui/", {"host": "elsewhere.example"}, 403),
    ],
)
def test_every_answer_carries_the_security_headers(
    api: httpx.Client, method: str, path: str, headers: dict[str, str], status: int
) -> None:
    response = api.request(method, path, headers=headers, json={} if method == "POST" else None)
    assert response.status_code == status, response.text
    assert_secured(response)


def test_a_streamed_turn_carries_the_security_headers(api: httpx.Client) -> None:
    with api.stream("POST", "/api/turns", json={"agent_id": "pydantic_ai", "text": "hi"}) as turn:
        assert turn.status_code == 200
        assert turn.headers["content-type"].startswith("text/event-stream")
        assert_secured(turn)
        turn.read()

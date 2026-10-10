# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers of ``docs/specs/frontend.md``: the files of
the interface, the API's answers, a streamed turn, and every kind of refusal, the ones the
guard gives before a route is reached included.

The values are spelled out here rather than imported, so that a header dropped from, or
weakened in, the list the server keeps fails this test instead of passing with it.
"""

from __future__ import annotations

import uuid

import httpx
import pytest

from util.controller_db import requires_postgres

pytestmark = requires_postgres

EXPECTED = {
    "content-security-policy": (
        "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        " img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none';"
        " form-action 'none'; frame-ancestors 'none'"
    ),
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "referrer-policy": "same-origin",
}

NOWHERE = uuid.UUID(int=0)

ANSWERS = [
    # (method, path, request headers, request body, the status it is answered with)
    ("GET", "/ui/", {}, None, 200),
    ("GET", "/ui/index.html", {}, None, 200),
    ("GET", "/ui/missing.js", {}, None, 404),
    ("GET", "/", {}, None, 307),
    ("GET", "/auth/session", {}, None, 200),
    ("GET", "/api/agents", {}, None, 200),
    ("GET", "/api/conversations", {}, None, 200),
    ("GET", f"/api/conversations/{NOWHERE}", {}, None, 404),
    ("GET", "/api/conversations/not-a-uuid", {}, None, 422),
    ("POST", "/api/turns", {}, {"text": 7}, 422),
    ("DELETE", "/api/conversations", {}, None, 405),
    ("GET", "/api/no-such-route", {}, None, 404),
    ("GET", "/api/conversations", {"host": "evil.example"}, None, 403),
    ("GET", "/ui/", {"host": "evil.example"}, None, 403),
    ("POST", "/api/turns", {"origin": "http://evil.example"}, {"text": "hi"}, 403),
]


def assert_secured(response: httpx.Response) -> None:
    carried = {name: response.headers.get(name) for name in EXPECTED}
    assert carried == EXPECTED, f"{response.request.method} {response.request.url}"


@pytest.mark.parametrize(
    ("method", "path", "headers", "body", "status"),
    ANSWERS,
    ids=[f"{m} {p} {s}{' ' + next(iter(h)) if h else ''}" for m, p, h, _, s in ANSWERS],
)
def test_an_answer_carries_the_security_headers(
    api: httpx.Client,
    method: str,
    path: str,
    headers: dict[str, str],
    body: object,
    status: int,
) -> None:
    response = api.request(method, path, headers=headers, json=body)
    assert response.status_code == status, response.text
    assert_secured(response)


def test_a_streamed_turn_carries_the_security_headers(api: httpx.Client) -> None:
    turn = {"agent_id": "pydantic_ai", "text": "hello"}
    with api.stream("POST", "/api/turns", json=turn) as streamed:
        assert streamed.status_code == 200
        assert streamed.headers["content-type"].startswith("text/event-stream")
        assert_secured(streamed)
        streamed.read()

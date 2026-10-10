# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: the interface's files, the API's answers,
a streamed turn, and the refusals of the guard, of a route and of the router. No browser shows
them on an answer it does not render, so they are asserted here."""

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

NOWHERE = str(uuid.uuid4())

ANSWERS = [
    pytest.param("GET", "/ui/", {}, None, 200, id="the interface's page"),
    pytest.param("GET", "/ui/missing.js", {}, None, 404, id="a file the interface lacks"),
    pytest.param("GET", "/", {}, None, 307, id="the redirect to the interface"),
    pytest.param("GET", "/health", {}, None, 200, id="health"),
    pytest.param("GET", "/api/agents", {}, None, 200, id="an API answer"),
    pytest.param("GET", f"/api/conversations/{NOWHERE}", {}, None, 404, id="an unknown id"),
    pytest.param("POST", "/api/turns", {}, {"text": 1}, 422, id="a malformed body"),
    pytest.param("GET", "/no/such/path", {}, None, 404, id="an unknown path"),
    pytest.param("DELETE", "/health", {}, None, 405, id="a method not allowed"),
    pytest.param("GET", "/api/agents", {"host": "rebound.example"}, None, 403, id="a foreign host"),
    pytest.param(
        "POST",
        "/api/turns",
        {"origin": "https://elsewhere.example"},
        {"agent_id": "pydantic_ai", "text": "hello"},
        403,
        id="a foreign origin",
    ),
]


def assert_secured(response: httpx.Response) -> None:
    carried = {name: response.headers.get(name) for name in SECURITY_HEADERS}
    assert carried == SECURITY_HEADERS, (response.request.method, response.request.url)


@pytest.mark.parametrize(("method", "path", "headers", "body", "status"), ANSWERS)
def test_every_answer_carries_the_security_headers(
    api: httpx.Client,
    method: str,
    path: str,
    headers: dict[str, str],
    body: object,
    status: int,
) -> None:
    response = api.request(method, path, headers=headers, json=body, follow_redirects=False)
    assert response.status_code == status, response.text
    assert_secured(response)


def test_a_streamed_turn_carries_the_security_headers(api: httpx.Client) -> None:
    turn = {"agent_id": "pydantic_ai", "text": "hello"}
    with api.stream("POST", "/api/turns", json=turn) as streamed:
        assert streamed.status_code == 200
        assert streamed.headers["content-type"].startswith("text/event-stream")
        assert_secured(streamed)
        streamed.read()

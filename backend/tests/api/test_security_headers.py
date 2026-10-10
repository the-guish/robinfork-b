# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: an answer, a stream, a redirect, the files
of the interface, and every kind of refusal, the ones the guard gives before any route too.

A browser shows none of them, so they are asserted here and not in ``tests/e2e``.
"""

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

ELSEWHERE = f"/api/conversations/{uuid.uuid4()}"

ASKED = [
    # what is asked, and the status it is answered with
    pytest.param("GET", "/api/agents", {}, None, 200, id="an-answer"),
    pytest.param("GET", "/", {}, None, 307, id="a-redirect"),
    pytest.param("GET", "/ui/", {}, None, 200, id="the-interface"),
    pytest.param("GET", "/ui/index.html", {}, None, 200, id="an-interface-file"),
    pytest.param("GET", "/ui/missing.js", {}, None, 404, id="no-interface-file"),
    pytest.param("GET", "/api/nowhere", {}, None, 404, id="no-route"),
    pytest.param("DELETE", "/api/agents", {}, None, 405, id="no-method"),
    pytest.param("GET", ELSEWHERE, {}, None, 404, id="no-conversation"),
    pytest.param("POST", "/api/turns", {}, {"text": 1}, 422, id="a-malformed-body"),
    pytest.param(
        "GET", "/api/agents", {"host": "robinauts.example.com"}, None, 403, id="a-foreign-host"
    ),
    pytest.param(
        "POST",
        "/api/turns",
        {"origin": "https://elsewhere.example.com"},
        {"agent_id": "pydantic_ai", "text": "hello"},
        403,
        id="a-foreign-origin",
    ),
    pytest.param(
        "GET", "/ui/", {"host": "robinauts.example.com"}, None, 403, id="the-interface-refused"
    ),
]


@pytest.mark.parametrize(("method", "path", "headers", "body", "status"), ASKED)
def test_every_answer_carries_the_security_headers(
    api: httpx.Client,
    method: str,
    path: str,
    headers: dict[str, str],
    body: object,
    status: int,
) -> None:
    answer = api.request(method, path, headers=headers, json=body)
    assert answer.status_code == status, answer.text
    assert {name: answer.headers.get(name) for name in SECURITY_HEADERS} == SECURITY_HEADERS


def test_a_streamed_turn_carries_the_security_headers(api: httpx.Client) -> None:
    turn = {"agent_id": "pydantic_ai", "text": "hello"}
    with api.stream("POST", "/api/turns", json=turn) as answer:
        assert answer.status_code == 200
        assert answer.headers["content-type"].startswith("text/event-stream")
        assert {name: answer.headers.get(name) for name in SECURITY_HEADERS} == SECURITY_HEADERS
        answer.read()

# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: the API's, its refusals of every kind and
the files of the interface. A browser shows none of them, so no e2e test can see they are
there."""

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

UNKNOWN = uuid.uuid4()

ANSWERS = [
    pytest.param("GET", "/health", {}, None, 200, id="health"),
    pytest.param("GET", "/api/conversations", {}, None, 200, id="api"),
    pytest.param("GET", "/ui/", {}, None, 200, id="interface"),
    pytest.param(
        "POST", "/api/turns", {}, {"agent_id": "pydantic_ai", "text": "hi"}, 200, id="event-stream"
    ),
    pytest.param("GET", f"/api/conversations/{UNKNOWN}", {}, None, 404, id="unknown-conversation"),
    pytest.param("GET", "/no/such/route", {}, None, 404, id="unknown-route"),
    pytest.param("GET", "/ui/no-such-file.js", {}, None, 404, id="unknown-interface-file"),
    pytest.param("POST", "/api/turns", {}, {"text": 1}, 422, id="malformed-body"),
    pytest.param("DELETE", "/health", {}, None, 405, id="wrong-method"),
    pytest.param(
        "GET", "/api/conversations", {"host": "example.com"}, None, 403, id="foreign-host"
    ),
    pytest.param(
        "POST",
        "/api/turns",
        {"origin": "https://example.com"},
        {"agent_id": "pydantic_ai", "text": "hi"},
        403,
        id="foreign-origin",
    ),
]


@pytest.mark.parametrize(("method", "path", "headers", "body", "status"), ANSWERS)
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

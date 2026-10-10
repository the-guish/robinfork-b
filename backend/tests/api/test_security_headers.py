# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: the interface's files, the API's answers,
and its refusals, whether the guard, a route or the framework gives them."""

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

MISSING = str(uuid.uuid4())

ANSWERS = [
    pytest.param("GET", "/ui/", {}, None, 200, id="interface-page"),
    pytest.param("GET", "/ui/missing.js", {}, None, 404, id="interface-missing-file"),
    pytest.param("GET", "/", {}, None, 307, id="redirect-to-interface"),
    pytest.param("GET", "/api/agents", {}, None, 200, id="api-answer"),
    pytest.param("GET", "/health", {}, None, 200, id="health"),
    pytest.param("GET", f"/api/conversations/{MISSING}", {}, None, 404, id="unknown-conversation"),
    pytest.param("POST", "/api/turns", {}, {"text": 1}, 422, id="invalid-body"),
    pytest.param("GET", "/no/such/path", {}, None, 404, id="unknown-path"),
    pytest.param("DELETE", "/health", {}, None, 405, id="wrong-method"),
    pytest.param("GET", "/api/agents", {"host": "example.com"}, None, 403, id="foreign-host"),
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
    answer = api.request(method, path, headers=headers, json=body, follow_redirects=False)

    assert answer.status_code == status, answer.text
    assert {name: answer.headers.get(name) for name in SECURITY_HEADERS} == SECURITY_HEADERS

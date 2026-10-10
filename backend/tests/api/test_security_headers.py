# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: the interface's files, the API's answers,
a stream, a redirect, and the refusals of the guard, of the routes and of the router alike.

A browser shows none of them, so this is not an e2e test.
"""

from __future__ import annotations

import uuid

import httpx
import pytest

from robinauts.web.headers import SECURITY_HEADERS
from util.controller_db import requires_postgres

pytestmark = requires_postgres

UNKNOWN = uuid.uuid4()

ANSWERS = {
    "the interface's page": ("GET", "/ui/", {}, None, 200),
    "the interface's index file": ("GET", "/ui/index.html", {}, None, 200),
    "a file the interface does not have": ("GET", "/ui/missing.js", {}, None, 404),
    "the redirect to the interface": ("GET", "/", {}, None, 307),
    "an API answer": ("GET", "/api/agents", {}, None, 200),
    "the health check": ("GET", "/health", {}, None, 200),
    "a stream of events": (
        "POST",
        "/api/turns",
        {},
        {"agent_id": "pydantic_ai", "text": "hi"},
        200,
    ),
    "an unknown conversation": ("GET", f"/api/conversations/{UNKNOWN}", {}, None, 404),
    "an unknown path": ("GET", "/api/nowhere", {}, None, 404),
    "a method a route does not take": ("PUT", "/api/agents", {}, None, 405),
    "a body that does not validate": ("POST", "/api/turns", {}, {"text": 1}, 422),
    "a request from another origin": (
        "POST",
        "/api/turns",
        {"origin": "https://elsewhere.example"},
        {"agent_id": "pydantic_ai", "text": "hi"},
        403,
    ),
    "a request for another host": ("GET", "/api/agents", {"host": "elsewhere.example"}, None, 403),
}


@pytest.mark.parametrize(
    ("method", "path", "headers", "body", "status"), ANSWERS.values(), ids=ANSWERS.keys()
)
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
    assert {name: answer.headers.get(name) for name, _ in SECURITY_HEADERS} == dict(
        SECURITY_HEADERS
    )

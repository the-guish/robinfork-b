# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: an API answer, a refusal, a redirect and the
files of the interface, found or not. No page shows a header, so this is not an ``e2e`` test."""

from __future__ import annotations

import uuid

import httpx
import pytest

from robinauts.web.headers import SECURITY_HEADERS
from util.controller_db import requires_postgres

pytestmark = requires_postgres

FOREIGN = "http://elsewhere.example"

ANSWERS = [
    pytest.param("GET", "/api/agents", {}, None, 200, id="an API answer"),
    pytest.param("GET", "/", {}, None, 307, id="the redirect to the interface"),
    pytest.param("GET", "/ui/", {}, None, 200, id="the interface"),
    pytest.param("GET", "/ui/assets/missing.js", {}, None, 404, id="a missing interface file"),
    pytest.param("GET", "/api/missing", {}, None, 404, id="a missing route"),
    pytest.param(
        "GET", f"/api/conversations/{uuid.uuid4()}", {}, None, 404, id="an unknown conversation"
    ),
    pytest.param("POST", "/api/turns", {}, {"text": 1}, 422, id="a malformed request"),
    pytest.param(
        "POST",
        "/api/turns",
        {"origin": FOREIGN},
        {"agent_id": "pydantic_ai", "text": "hello"},
        403,
        id="a cross-origin request",
    ),
    pytest.param("GET", "/ui/", {"host": "elsewhere.example"}, None, 403, id="a foreign host"),
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
    assert {name: answer.headers.get(name) for name, _ in SECURITY_HEADERS} == dict(
        SECURITY_HEADERS
    )

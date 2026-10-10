# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: the API's, its refusals, its redirects and
the files of the interface. A browser applies them without showing them, so the UI cannot."""

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

NO_SUCH_CONVERSATION = f"/api/conversations/{uuid.uuid4()}"

ANSWERS = [
    pytest.param("GET", "/ui/", {}, 200, id="the interface"),
    pytest.param("GET", "/ui/index.html", {}, 200, id="a file of the interface"),
    pytest.param("GET", "/ui/no-such-file.js", {}, 404, id="no such file of the interface"),
    pytest.param("GET", "/", {}, 307, id="a redirect to the interface"),
    pytest.param("GET", "/api/conversations", {}, 200, id="an API answer"),
    pytest.param("GET", "/health", {}, 200, id="health"),
    pytest.param("GET", "/no/such/route", {}, 404, id="no such route"),
    pytest.param("GET", NO_SUCH_CONVERSATION, {}, 404, id="no such conversation"),
    pytest.param("GET", "/api/conversations/not-a-uuid", {}, 422, id="an invalid request"),
    pytest.param(
        "GET", "/ui/", {"host": "rebound.example"}, 403, id="the interface to a foreign host"
    ),
    pytest.param(
        "GET", "/api/conversations", {"host": "rebound.example"}, 403, id="a foreign host"
    ),
    pytest.param(
        "DELETE",
        NO_SUCH_CONVERSATION,
        {"origin": "https://elsewhere.example"},
        403,
        id="a write from a foreign origin",
    ),
]


@pytest.mark.parametrize(("method", "path", "headers", "status"), ANSWERS)
def test_every_answer_carries_the_security_headers(
    api: httpx.Client, method: str, path: str, headers: dict[str, str], status: int
) -> None:
    response = api.request(method, path, headers=headers)

    assert response.status_code == status, response.text
    carried = {name: response.headers.get(name) for name in SECURITY_HEADERS}
    assert carried == SECURITY_HEADERS

# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""Every HTTP answer carries the security headers: the interface's files, the API's answers
and its refusals, whichever layer refuses. A browser shows none of them, so the UI cannot."""

from __future__ import annotations

import uuid

import httpx
import pytest

from robinauts.web.headers import SECURITY_HEADERS
from util.controller_db import requires_postgres

pytestmark = requires_postgres

ANSWERS = {
    "the interface's page": ("GET", "/ui/", {}, 200),
    "a file the interface lacks": ("GET", "/ui/no-such-file.js", {}, 404),
    "the way to the interface": ("GET", "/", {}, 307),
    "an API answer": ("GET", "/api/agents", {}, 200),
    "a conversation that is not there": ("GET", f"/api/conversations/{uuid.uuid4()}", {}, 404),
    "a malformed id": ("GET", "/api/conversations/not-an-id", {}, 422),
    "a route that is not there": ("GET", "/api/no-such-route", {}, 404),
    "a request from another site": (
        "POST",
        "/api/turns",
        {"origin": "https://elsewhere.example"},
        403,
    ),
}


@pytest.mark.parametrize(
    ("method", "path", "headers", "status"), ANSWERS.values(), ids=ANSWERS.keys()
)
def test_every_answer_carries_the_security_headers(
    api: httpx.Client, method: str, path: str, headers: dict[str, str], status: int
) -> None:
    answer = api.request(method, path, headers=headers)
    assert answer.status_code == status, answer.text
    for name, value in SECURITY_HEADERS:
        assert answer.headers.get(name) == value, name

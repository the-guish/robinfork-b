# SPDX-License-Identifier: Apache-2.0
# Copyright The Robinauts Authors

"""The fast run of tests/api/test_security_headers.py: the headers on an answer, on the
interface, and on the refusals of the guard, of a route and of the static files."""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx
from echo_controller import CONFIG

from robinauts.controller.composition import compose
from robinauts.controller.contract.domain import StorageConfig, StorageKind
from robinauts.web.app import create_app
from util.aio import asyncio_test

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


@asyncio_test
async def test_every_answer_carries_the_security_headers(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<!doctype html><title>Robinauts</title>")
    composed = compose(CONFIG, storage=StorageConfig(StorageKind.IN_MEMORY), secret_for={}.get)
    app = create_app(composed, sign_in=None, secret_for={}.get, ui_dir=tmp_path)
    foreign = {"host": "robinauts.example.com"}
    asked = [
        ("GET", "/api/agents", {}, 200),
        ("GET", "/", {}, 307),
        ("GET", "/ui/", {}, 200),
        ("GET", "/ui/missing.js", {}, 404),
        ("GET", f"/api/conversations/{uuid.uuid4()}", {}, 404),
        ("DELETE", "/api/agents", {}, 405),
        ("GET", "/api/agents", foreign, 403),
        ("GET", "/ui/", foreign, 403),
    ]
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1") as http:
            for method, path, headers, status in asked:
                answer = await http.request(method, path, headers=headers)
                assert answer.status_code == status, (method, path, answer.text)
                carried = {name: answer.headers.get(name) for name in SECURITY_HEADERS}
                assert carried == SECURITY_HEADERS, (method, path)

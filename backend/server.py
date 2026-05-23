"""
Thin HTTP proxy. Forwards /api/* (and any other path) to the upstream
InnerCore backend specified by UPSTREAM_API (env or default).

Purpose: lets the SPA served from this preview environment talk to the user's
external HTTP backend without running into Mixed Content / CORS in the browser.

This is dev convenience only — production deployment should hit the backend
directly.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

UPSTREAM = os.environ.get("UPSTREAM_API", "http://89.125.77.243:8080").rstrip("/")

app = FastAPI(title="InnerCore Web Proxy", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
    "content-encoding", "accept-encoding",
}


@app.get("/health")
async def health():
    return {"status": "ok", "upstream": UPSTREAM}


@app.get("/")
async def root():
    return {"service": "innercore-web-proxy", "upstream": UPSTREAM}


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy(path: str, request: Request) -> Response:
    target = f"{UPSTREAM}/api/{path}"

    fwd_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP and k.lower() != "origin"
    }
    fwd_headers.setdefault("X-App-Version", request.headers.get("x-app-version", "0.4.2"))

    body = await request.body()
    params = dict(request.query_params)

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=False) as client:
        try:
            up = await client.request(
                request.method,
                target,
                params=params,
                headers=fwd_headers,
                content=body if body else None,
            )
        except httpx.RequestError as e:
            return Response(
                content=f'{{"detail":"upstream_unreachable","error":"{type(e).__name__}: {e}"}}',
                status_code=502,
                media_type="application/json",
            )

    resp_headers = {
        k: v for k, v in up.headers.items()
        if k.lower() not in HOP_BY_HOP
    }
    return Response(content=up.content, status_code=up.status_code, headers=resp_headers, media_type=up.headers.get("content-type"))

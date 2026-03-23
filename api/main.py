"""
REST API for Tennis League. OpenAPI (Swagger) at /docs.
"""
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.limiter import limiter
from api.routers import auth, client_sessions, divisions, game_requests, matches, players, seasons

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tennis League API",
    description="REST API for Лига настольного тенниса",
    version="1.0.0",
)

# CORS: только доверенные origin'ы из env (OWASP)
_cors_origins_raw = (os.getenv("CORS_ORIGINS") or "").strip()
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

app.state.limiter = limiter
from slowapi import _rate_limit_exceeded_handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Log 401/403 access denials (OWASP: minimal context, no secrets)."""
    if exc.status_code in (401, 403):
        logger.warning(
            "Access denied: status=%s path=%s detail=%s",
            exc.status_code,
            request.url.path,
            exc.detail,
        )
    from starlette.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/")
def root():
    return {"message": "Tennis League API", "docs": "/docs", "docs_supabase": "/docs-supabase"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(players.router)
app.include_router(seasons.router)
app.include_router(divisions.router)
app.include_router(matches.router)
app.include_router(game_requests.router)
app.include_router(client_sessions.router)


def _supabase_openapi_path() -> Path:
    return Path(__file__).resolve().parent.parent / "docs" / "openapi-supabase.yaml"


@app.get("/openapi-supabase.yaml", response_class=PlainTextResponse)
def openapi_supabase_yaml():
    """Serve OpenAPI spec for Supabase (frontend) operations."""
    path = _supabase_openapi_path()
    if not path.exists():
        return PlainTextResponse(content="# OpenAPI spec not found\n", status_code=404)
    return PlainTextResponse(content=path.read_text(encoding="utf-8"), media_type="application/x-yaml")


@app.get("/docs-supabase", response_class=HTMLResponse)
def docs_supabase_html():
    """Swagger UI for Supabase API reference (logical operations from frontend)."""
    path = _supabase_openapi_path()
    if not path.exists():
        return HTMLResponse(
            "<!DOCTYPE html><html><body><p>OpenAPI spec not found. Create docs/openapi-supabase.yaml</p></body></html>",
            status_code=404,
        )
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Supabase API Reference — Tennis League</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/openapi-supabase.yaml",
      dom_id: "#swagger-ui",
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
      ]
    });
  </script>
</body>
</html>"""
    )

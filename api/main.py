"""
REST API for Tennis League. OpenAPI (Swagger) at /docs.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

from api.routers import divisions, matches, players, seasons

app = FastAPI(
    title="Tennis League API",
    description="REST API for Лига настольного тенниса",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Tennis League API", "docs": "/docs", "docs_supabase": "/docs-supabase"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(players.router)
app.include_router(seasons.router)
app.include_router(divisions.router)
app.include_router(matches.router)


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

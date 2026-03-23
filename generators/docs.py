"""Dokumentation-Generatoren: README, License, Changelog, Contributing."""

from datetime import date
from jinja2 import Environment, FileSystemLoader

from . import register, TEMPLATE_DIR, get_output_dir

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR / "docs"), keep_trailing_newline=True)


@register(
    name="readme",
    category="Dokumentation",
    description="Generiert eine README.md mit Projekt-Info, Badges und Sections",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "description", "type": "text", "description": "Kurzbeschreibung des Projekts", "required": True},
        {"name": "stack", "type": "select", "options": ["python", "node", "java", "go", "other"],
         "description": "Tech-Stack", "required": False},
        {"name": "license_type", "type": "select", "options": ["MIT", "Apache-2.0", "GPL-3.0", ""],
         "description": "Lizenztyp für Badge", "required": False},
        {"name": "badges", "type": "boolean", "description": "Badges anzeigen", "required": False},
        {"name": "has_api", "type": "boolean", "description": "API-Section inkludieren", "required": False},
        {"name": "has_env", "type": "boolean", "description": ".env-Section inkludieren", "required": False},
    ],
)
def generate_readme(params: dict) -> dict:
    tmpl = env.get_template("readme.md.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / "README.md"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": "README.md generiert"}


@register(
    name="license",
    category="Dokumentation",
    description="Generiert eine LICENSE Datei (MIT, Apache, GPL)",
    parameters=[
        {"name": "license_type", "type": "select", "options": ["mit", "apache", "gpl"],
         "description": "Lizenztyp", "required": True},
        {"name": "author", "type": "text", "description": "Autor / Copyright Holder", "required": True},
        {"name": "year", "type": "text", "description": "Copyright Jahr", "required": False},
    ],
)
def generate_license(params: dict) -> dict:
    license_type = params.get("license_type", "mit")
    if not params.get("year"):
        params["year"] = str(date.today().year)
    tmpl = env.get_template(f"license/{license_type}.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / "LICENSE"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"LICENSE ({license_type.upper()}) generiert"}


@register(
    name="changelog",
    category="Dokumentation",
    description="Generiert ein CHANGELOG.md im Keep-a-Changelog Format",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
    ],
)
def generate_changelog(params: dict) -> dict:
    params["date"] = str(date.today())
    tmpl = env.get_template("changelog.md.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / "CHANGELOG.md"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": "CHANGELOG.md generiert"}


@register(
    name="contributing",
    category="Dokumentation",
    description="Generiert eine CONTRIBUTING.md mit Richtlinien",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "stack", "type": "select", "options": ["python", "node", "java", "go", "other"],
         "description": "Tech-Stack", "required": False},
    ],
)
def generate_contributing(params: dict) -> dict:
    tmpl = env.get_template("contributing.md.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / "CONTRIBUTING.md"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": "CONTRIBUTING.md generiert"}


# ── OpenAPI Spec ──────────────────────────────────────────

@register(
    name="openapi-spec",
    category="Dokumentation",
    description="Generiert eine OpenAPI 3.0 Spezifikation (YAML)",
    parameters=[
        {"name": "title", "type": "text", "description": "API-Titel", "required": True},
        {"name": "version", "type": "text", "description": "API-Version", "required": False, "default": "1.0.0"},
        {"name": "description", "type": "text", "description": "API-Beschreibung", "required": False},
        {"name": "base_url", "type": "text", "description": "Server-URL", "required": False, "default": "http://localhost:3000"},
        {"name": "endpoints", "type": "multi-select",
         "options": ["health", "auth", "users", "items", "upload"],
         "description": "Beispiel-Endpoints", "required": False},
    ],
)
def generate_openapi_spec(params: dict) -> dict:
    title = params.get("title", "My API")
    version = params.get("version", "1.0.0")
    desc = params.get("description", f"{title} API Documentation")
    base_url = params.get("base_url", "http://localhost:3000")
    endpoints = params.get("endpoints", ["health"])
    if isinstance(endpoints, str):
        endpoints = [endpoints] if endpoints else []

    lines = [
        "openapi: '3.0.3'",
        "info:",
        f"  title: {title}",
        f"  version: '{version}'",
        f"  description: {desc}",
        "servers:",
        f"  - url: {base_url}",
        "paths:",
    ]

    endpoint_defs = {
        "health": """  /health:
    get:
      summary: Health Check
      tags: [System]
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: ok""",
        "auth": """  /auth/login:
    post:
      summary: Login
      tags: [Auth]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login erfolgreich
        '401':
          description: Ungültige Anmeldedaten
  /auth/register:
    post:
      summary: Registrierung
      tags: [Auth]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                name:
                  type: string
                password:
                  type: string
      responses:
        '201':
          description: Benutzer erstellt""",
        "users": """  /users:
    get:
      summary: Alle Benutzer auflisten
      tags: [Users]
      responses:
        '200':
          description: Liste der Benutzer
  /users/{id}:
    get:
      summary: Benutzer nach ID
      tags: [Users]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Benutzer gefunden
        '404':
          description: Nicht gefunden""",
        "items": """  /items:
    get:
      summary: Alle Items auflisten
      tags: [Items]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Liste der Items
    post:
      summary: Neues Item erstellen
      tags: [Items]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                description:
                  type: string
      responses:
        '201':
          description: Item erstellt""",
        "upload": """  /upload:
    post:
      summary: Datei hochladen
      tags: [Upload]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
      responses:
        '200':
          description: Upload erfolgreich""",
    }

    for ep in endpoints:
        if ep in endpoint_defs:
            lines.append(endpoint_defs[ep])

    if not endpoints:
        lines.append("  {}  # No endpoints defined")

    content = "\n".join(lines) + "\n"
    out = get_output_dir() / "openapi.yaml"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"OpenAPI Spec generiert ({len(endpoints)} Endpoints)"}

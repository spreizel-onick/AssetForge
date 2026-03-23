"""Datenbank-Generatoren: Schema, Migration, Seed Data, ERD."""

from datetime import date
from jinja2 import Environment, FileSystemLoader

from . import register, TEMPLATE_DIR, get_output_dir

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR / "database"), keep_trailing_newline=True)


@register(
    name="schema",
    category="Datenbank",
    description="Generiert SQL CREATE TABLE Statements",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "tables", "type": "json", "description": (
            'Liste von Tabellen. Format: [{"name": "users", "columns": [{"name": "email", "type": "varchar(255)", '
            '"nullable": false}], "timestamps": true}]'
        ), "required": True},
        {"name": "foreign_keys", "type": "json", "description": (
            'Foreign Keys. Format: [{"table": "posts", "column": "user_id", "references_table": "users"}]'
        ), "required": False},
    ],
)
def generate_schema(params: dict) -> dict:
    tmpl = env.get_template("schema.sql.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / "schema.sql"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"Schema generiert mit {len(params.get('tables', []))} Tabelle(n)"}


@register(
    name="migration",
    category="Datenbank",
    description="Generiert eine SQL-Migration (create_table, add_column, drop_table)",
    parameters=[
        {"name": "migration_name", "type": "text", "description": "Name der Migration", "required": True},
        {"name": "migration_type", "type": "select", "options": ["create_table", "add_column", "drop_table"],
         "description": "Typ der Migration", "required": True},
        {"name": "table_name", "type": "text", "description": "Tabellenname", "required": True},
        {"name": "columns", "type": "json", "description": (
            'Spalten. Format: [{"name": "email", "type": "varchar(255)", "nullable": false}]'
        ), "required": False},
    ],
)
def generate_migration(params: dict) -> dict:
    params["date"] = str(date.today())
    tmpl = env.get_template("migration.j2")
    content = tmpl.render(**params)
    name = params.get("migration_name", "migration").replace(" ", "_").lower()
    out = get_output_dir() / f"migration_{name}.sql"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"Migration '{name}' generiert"}


@register(
    name="seed",
    category="Datenbank",
    description="Generiert SQL INSERT Statements als Seed Data",
    parameters=[
        {"name": "table_name", "type": "text", "description": "Tabellenname", "required": True},
        {"name": "rows", "type": "json", "description": (
            'Zeilen als Liste von Dicts. Format: [{"name": "Alice", "email": "alice@example.com"}]'
        ), "required": True},
    ],
)
def generate_seed(params: dict) -> dict:
    tmpl = env.get_template("seed.j2")
    content = tmpl.render(**params)
    table = params.get("table_name", "table")
    out = get_output_dir() / f"seed_{table}.sql"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"Seed Data für '{table}' generiert"}


@register(
    name="erd",
    category="Datenbank",
    description="Generiert ein Entity-Relationship-Diagramm als Mermaid-Markdown",
    parameters=[
        {"name": "tables", "type": "json", "description": (
            'Tabellen mit Spalten. Format: [{"name": "users", "columns": [{"name": "id", "type": "int"}, '
            '{"name": "email", "type": "varchar"}]}]'
        ), "required": True},
        {"name": "relations", "type": "json", "description": (
            'Beziehungen. Format: [{"from": "users", "to": "posts", "type": "1-to-many"}]'
        ), "required": False},
    ],
)
def generate_erd(params: dict) -> dict:
    tables = params.get("tables", [])
    relations = params.get("relations", [])

    lines = ["```mermaid", "erDiagram"]
    for table in tables:
        lines.append(f"    {table['name']} {{")
        for col in table.get("columns", []):
            lines.append(f"        {col['type']} {col['name']}")
        lines.append("    }")

    relation_map = {"1-to-1": "||--||", "1-to-many": "||--o{", "many-to-many": "}o--o{"}
    for rel in relations:
        symbol = relation_map.get(rel.get("type", "1-to-many"), "||--o{")
        label = rel.get("label", "")
        lines.append(f"    {rel['from']} {symbol} {rel['to']} : \"{label}\"")

    lines.append("```")
    content = "\n".join(lines)
    out = get_output_dir() / "erd.md"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": "ERD (Mermaid) generiert"}

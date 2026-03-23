"""Config-Generatoren: Gitignore, Dockerfile, Docker-Compose, .env, CI/CD und mehr."""

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from . import register, TEMPLATE_DIR, get_output_dir

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR / "config"), keep_trailing_newline=True)


# ── Gitignore ──────────────────────────────────────────────

GITIGNORE_TEMPLATES = {
    "python": [
        "__pycache__/", "*.py[cod]", "*$py.class", "*.so", ".Python", "env/", "venv/",
        ".venv/", "*.egg-info/", "dist/", "build/", ".eggs/", "*.egg", ".mypy_cache/",
        ".pytest_cache/", ".tox/", "htmlcov/", ".coverage", "*.log",
    ],
    "node": [
        "node_modules/", "dist/", "build/", ".next/", ".nuxt/", "*.log", "npm-debug.log*",
        ".env", ".env.local", ".env.*.local", "coverage/", ".cache/",
    ],
    "java": [
        "*.class", "*.jar", "*.war", "*.ear", "target/", ".gradle/", "build/",
        ".idea/", "*.iml", "out/", ".settings/", ".project", ".classpath",
    ],
    "general": [
        ".DS_Store", "Thumbs.db", "*.swp", "*.swo", "*~", ".vscode/", ".idea/",
        "*.env", "*.log",
    ],
}


@register(
    name="gitignore",
    category="Konfiguration",
    description="Generiert eine .gitignore Datei für den gewählten Tech-Stack",
    parameters=[
        {"name": "stacks", "type": "multi-select", "options": list(GITIGNORE_TEMPLATES.keys()),
         "description": "Tech-Stacks für die Gitignore-Regeln", "required": True},
        {"name": "custom_entries", "type": "text", "description": "Zusätzliche Einträge (eins pro Zeile)", "required": False},
    ],
)
def generate_gitignore(params: dict) -> dict:
    stacks = params.get("stacks", ["general"])
    if isinstance(stacks, str):
        stacks = [stacks]
    custom = params.get("custom_entries", "")

    lines = ["# Auto-generated .gitignore", ""]
    for stack in stacks:
        entries = GITIGNORE_TEMPLATES.get(stack, [])
        if entries:
            lines.append(f"# === {stack.title()} ===")
            lines.extend(entries)
            lines.append("")

    if custom and custom.strip():
        lines.append("# === Custom ===")
        lines.extend(custom.strip().splitlines())
        lines.append("")

    content = "\n".join(lines)
    out = get_output_dir() / ".gitignore"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f".gitignore generiert für: {', '.join(stacks)}"}


# ── Dockerfile ─────────────────────────────────────────────

@register(
    name="dockerfile",
    category="Konfiguration",
    description="Generiert ein Dockerfile für den gewählten Stack",
    parameters=[
        {"name": "stack", "type": "select", "options": ["python", "node", "java", "go", "rust"],
         "description": "Programmiersprache / Runtime", "required": True},
        {"name": "port", "type": "number", "description": "Exponierter Port", "required": False, "default": 8000},
    ],
)
def generate_dockerfile(params: dict) -> dict:
    tmpl = env.get_template("dockerfile.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / "Dockerfile"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"Dockerfile generiert für {params.get('stack', 'python')}"}


# ── Docker Compose ─────────────────────────────────────────

@register(
    name="compose",
    category="Konfiguration",
    description="Generiert eine docker-compose.yml mit wählbaren Services",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "services", "type": "multi-select",
         "options": ["app", "postgres", "mysql", "redis", "mongo", "nginx"],
         "description": "Services die inkludiert werden sollen", "required": True},
        {"name": "port", "type": "number", "description": "App-Port", "required": False, "default": 8000},
    ],
)
def generate_compose(params: dict) -> dict:
    tmpl = env.get_template("docker-compose.yml.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / "docker-compose.yml"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": "docker-compose.yml generiert"}


# ── .env Template ──────────────────────────────────────────

@register(
    name="env",
    category="Konfiguration",
    description="Generiert ein .env.example Template",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "variables", "type": "text",
         "description": "Variablen (KEY=default_value, eins pro Zeile)", "required": False},
        {"name": "include_db", "type": "boolean", "description": "Datenbank-Variablen inkludieren", "required": False},
        {"name": "include_auth", "type": "boolean", "description": "Auth-Variablen inkludieren", "required": False},
    ],
)
def generate_env(params: dict) -> dict:
    tmpl = env.get_template("env.example.j2")
    content = tmpl.render(**params)
    out = get_output_dir() / ".env.example"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": ".env.example generiert"}


# ── CI/CD ──────────────────────────────────────────────────

@register(
    name="ci",
    category="Konfiguration",
    description="Generiert eine CI/CD Pipeline (GitHub Actions oder GitLab CI)",
    parameters=[
        {"name": "platform", "type": "select", "options": ["github", "gitlab"],
         "description": "CI/CD Plattform", "required": True},
        {"name": "stack", "type": "select", "options": ["python", "node", "java", "go"],
         "description": "Programmiersprache", "required": True},
        {"name": "run_tests", "type": "boolean", "description": "Tests ausführen", "required": False},
        {"name": "run_lint", "type": "boolean", "description": "Linting ausführen", "required": False},
        {"name": "deploy", "type": "boolean", "description": "Deploy-Step inkludieren", "required": False},
    ],
)
def generate_ci(params: dict) -> dict:
    platform = params.get("platform", "github")
    if platform == "github":
        tmpl = env.get_template("ci/github-actions.yml.j2")
        filename = ".github/workflows/ci.yml"
    else:
        tmpl = env.get_template("ci/gitlab-ci.yml.j2")
        filename = ".gitlab-ci.yml"
    content = tmpl.render(**params)
    out_path = get_output_dir() / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return {"files": [str(out_path)], "message": f"CI/CD Pipeline generiert ({platform})"}


# ── package.json ───────────────────────────────────────

@register(
    name="package-json",
    category="Konfiguration",
    description="Generiert eine package.json für Node.js-Projekte",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "description", "type": "text", "description": "Beschreibung", "required": False},
        {"name": "author", "type": "text", "description": "Autor", "required": False},
        {"name": "license", "type": "select", "options": ["MIT", "Apache-2.0", "GPL-3.0", "ISC"],
         "description": "Lizenz", "required": False},
        {"name": "type", "type": "select", "options": ["module", "commonjs"],
         "description": "Module-System", "required": False},
    ],
)
def generate_package_json(params: dict) -> dict:
    import json
    name = params.get("project_name", "my-app").lower().replace(" ", "-")
    pkg = {
        "name": name,
        "version": "0.1.0",
        "description": params.get("description", ""),
        "main": "index.js",
        "type": params.get("type", "module"),
        "scripts": {
            "start": "node index.js",
            "dev": "node --watch index.js",
            "test": "echo \"Error: no test specified\" && exit 1",
            "lint": "eslint .",
        },
        "keywords": [],
        "author": params.get("author", ""),
        "license": params.get("license", "MIT"),
    }
    content = json.dumps(pkg, indent=2, ensure_ascii=False)
    out = get_output_dir() / "package.json"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"package.json generiert für '{name}'"}


# ── pyproject.toml ─────────────────────────────────────

@register(
    name="pyproject",
    category="Konfiguration",
    description="Generiert eine pyproject.toml für Python-Projekte",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "description", "type": "text", "description": "Beschreibung", "required": False},
        {"name": "author", "type": "text", "description": "Autor", "required": False},
        {"name": "python_version", "type": "select", "options": ["3.10", "3.11", "3.12", "3.13"],
         "description": "Minimale Python-Version", "required": False},
        {"name": "framework", "type": "select", "options": ["none", "fastapi", "flask", "django"],
         "description": "Framework (wird als Dependency hinzugefügt)", "required": False},
    ],
)
def generate_pyproject(params: dict) -> dict:
    name = params.get("project_name", "my-project").lower().replace(" ", "-")
    py_ver = params.get("python_version", "3.10")
    author = params.get("author", "")
    desc = params.get("description", "")
    framework = params.get("framework", "none")

    deps = []
    if framework == "fastapi":
        deps.extend(['"fastapi>=0.115"', '"uvicorn>=0.34"'])
    elif framework == "flask":
        deps.append('"flask>=3.0"')
    elif framework == "django":
        deps.append('"django>=5.0"')

    deps_str = ", ".join(deps)

    content = f'''[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "{desc}"
readme = "README.md"
requires-python = ">={py_ver}"
license = {{text = "MIT"}}
authors = [{{name = "{author}"}}]
dependencies = [{deps_str}]

[project.optional-dependencies]
dev = ["pytest", "ruff"]

[tool.ruff]
line-length = 100
target-version = "py{py_ver.replace('.', '')}"

[tool.pytest.ini_options]
testpaths = ["tests"]
'''
    out = get_output_dir() / "pyproject.toml"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"pyproject.toml generiert für '{name}'"}


# ── tsconfig.json ──────────────────────────────────────

@register(
    name="tsconfig",
    category="Konfiguration",
    description="Generiert eine tsconfig.json für TypeScript-Projekte",
    parameters=[
        {"name": "target", "type": "select", "options": ["ES2020", "ES2022", "ESNext"],
         "description": "Compile Target", "required": False},
        {"name": "module", "type": "select", "options": ["ESNext", "NodeNext", "CommonJS"],
         "description": "Module-System", "required": False},
        {"name": "framework", "type": "select", "options": ["none", "react", "next", "node"],
         "description": "Framework (passt Optionen an)", "required": False},
        {"name": "strict", "type": "boolean", "description": "Strict Mode aktivieren", "required": False},
    ],
)
def generate_tsconfig(params: dict) -> dict:
    import json
    target = params.get("target", "ES2022")
    module = params.get("module", "ESNext")
    framework = params.get("framework", "none")
    strict = params.get("strict", True)

    config = {
        "compilerOptions": {
            "target": target,
            "module": module,
            "moduleResolution": "bundler" if module == "ESNext" else "node",
            "strict": strict,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "outDir": "./dist",
            "rootDir": "./src",
            "declaration": True,
        },
        "include": ["src/**/*"],
        "exclude": ["node_modules", "dist"],
    }

    if framework == "react" or framework == "next":
        config["compilerOptions"]["jsx"] = "react-jsx"
        config["compilerOptions"]["lib"] = ["dom", "dom.iterable", target]
    elif framework == "node":
        config["compilerOptions"]["module"] = "NodeNext"
        config["compilerOptions"]["moduleResolution"] = "nodenext"
        config["compilerOptions"]["lib"] = [target]

    content = json.dumps(config, indent=2)
    out = get_output_dir() / "tsconfig.json"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"tsconfig.json generiert ({target}, {framework})"}


# ── EditorConfig ──────────────────────────────────────────

@register(
    name="editorconfig",
    category="Konfiguration",
    description="Generiert eine .editorconfig für einheitliche Code-Formatierung",
    parameters=[
        {"name": "indent_style", "type": "select", "options": ["space", "tab"],
         "description": "Einrückungsstil", "required": False},
        {"name": "indent_size", "type": "select", "options": ["2", "4"],
         "description": "Einrückungsgröße", "required": False},
        {"name": "end_of_line", "type": "select", "options": ["lf", "crlf"],
         "description": "Zeilenende", "required": False},
    ],
)
def generate_editorconfig(params: dict) -> dict:
    style = params.get("indent_style", "space")
    size = params.get("indent_size", "2")
    eol = params.get("end_of_line", "lf")

    content = f"""root = true

[*]
indent_style = {style}
indent_size = {size}
end_of_line = {eol}
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
"""
    out = get_output_dir() / ".editorconfig"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f".editorconfig generiert ({style}, {size})"}


# ── Makefile ──────────────────────────────────────────────

@register(
    name="makefile",
    category="Konfiguration",
    description="Generiert ein Makefile mit gängigen Build-Targets",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "stack", "type": "select", "options": ["python", "node", "go"],
         "description": "Tech-Stack", "required": False},
    ],
)
def generate_makefile(params: dict) -> dict:
    name = params.get("project_name", "myproject")
    stack = params.get("stack", "python")

    targets = {
        "python": f""".PHONY: install dev test lint clean build run

install:
\tpip install -r requirements.txt

dev:
\tpip install -r requirements-dev.txt

test:
\tpytest tests/ -v

lint:
\truff check . && ruff format --check .

clean:
\trm -rf __pycache__ .pytest_cache .mypy_cache dist build *.egg-info

build:
\tpython -m build

run:
\tpython -m {name}
""",
        "node": f""".PHONY: install dev test lint clean build start

install:
\tnpm install

dev:
\tnpm run dev

test:
\tnpm test

lint:
\tnpm run lint

clean:
\trm -rf node_modules dist .next .nuxt

build:
\tnpm run build

start:
\tnpm start
""",
        "go": f""".PHONY: build test lint clean run

BINARY={name}

build:
\tgo build -o $(BINARY) ./cmd/$(BINARY)

test:
\tgo test ./... -v

lint:
\tgolangci-lint run

clean:
\trm -f $(BINARY)

run: build
\t./$(BINARY)
""",
    }

    content = targets.get(stack, targets["python"])
    out = get_output_dir() / "Makefile"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"Makefile generiert ({stack})"}


# ── .dockerignore ─────────────────────────────────────────

DOCKERIGNORE_TEMPLATES = {
    "python": [
        "__pycache__/", "*.py[cod]", "*.so", ".venv/", "venv/", "env/",
        ".mypy_cache/", ".pytest_cache/", "*.egg-info/", "dist/", "build/",
    ],
    "node": [
        "node_modules/", "npm-debug.log*", ".next/", ".nuxt/", "dist/", "build/", "coverage/",
    ],
    "general": [
        ".git", ".gitignore", ".dockerignore", "Dockerfile", "docker-compose*.yml",
        "*.md", "LICENSE", ".vscode/", ".idea/", ".env", ".env.*", "*.log",
        ".DS_Store", "Thumbs.db",
    ],
}


@register(
    name="dockerignore",
    category="Konfiguration",
    description="Generiert eine .dockerignore für schlankere Docker-Images",
    parameters=[
        {"name": "stacks", "type": "multi-select", "options": ["python", "node", "general"],
         "description": "Stacks (mehrere wählbar)", "required": True},
    ],
)
def generate_dockerignore(params: dict) -> dict:
    stacks = params.get("stacks", ["general"])
    if isinstance(stacks, str):
        stacks = [stacks]

    lines = ["# .dockerignore — generated by AssetForge", ""]
    for stack in stacks:
        entries = DOCKERIGNORE_TEMPLATES.get(stack, [])
        if entries:
            lines.append(f"# {stack}")
            lines.extend(entries)
            lines.append("")

    out = get_output_dir() / ".dockerignore"
    out.write_text("\n".join(lines), encoding="utf-8")
    return {"files": [str(out)], "message": f".dockerignore generiert ({', '.join(stacks)})"}


# ── Prettier Config ───────────────────────────────────────

@register(
    name="prettierrc",
    category="Konfiguration",
    description="Generiert eine .prettierrc für Code-Formatierung",
    parameters=[
        {"name": "semi", "type": "boolean", "description": "Semikolons verwenden", "required": False},
        {"name": "single_quote", "type": "boolean", "description": "Einfache Anführungszeichen", "required": False},
        {"name": "tab_width", "type": "select", "options": ["2", "4"],
         "description": "Tab-Breite", "required": False},
        {"name": "trailing_comma", "type": "select", "options": ["all", "es5", "none"],
         "description": "Trailing Commas", "required": False},
        {"name": "print_width", "type": "number", "description": "Zeilenbreite", "required": False, "default": 80},
    ],
)
def generate_prettierrc(params: dict) -> dict:
    config = {
        "semi": params.get("semi", True),
        "singleQuote": params.get("single_quote", False),
        "tabWidth": int(params.get("tab_width", "2")),
        "trailingComma": params.get("trailing_comma", "es5"),
        "printWidth": int(params.get("print_width", 80)),
        "arrowParens": "always",
        "endOfLine": "lf",
    }

    content = json.dumps(config, indent=2)
    out = get_output_dir() / ".prettierrc"
    out.write_text(content, encoding="utf-8")

    # Also generate .prettierignore
    ignore_lines = [
        "node_modules/", "dist/", "build/", "coverage/",
        ".next/", ".nuxt/", "*.min.js", "*.min.css",
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ]
    ignore_out = get_output_dir() / ".prettierignore"
    ignore_out.write_text("\n".join(ignore_lines) + "\n", encoding="utf-8")

    return {"files": [str(out), str(ignore_out)], "message": f".prettierrc + .prettierignore generiert"}


# ── Nginx Config ──────────────────────────────────────────

@register(
    name="nginx-conf",
    category="Konfiguration",
    description="Generiert eine nginx.conf für Reverse-Proxy oder Static-Hosting",
    parameters=[
        {"name": "mode", "type": "select", "options": ["reverse-proxy", "static", "spa"],
         "description": "Modus", "required": False},
        {"name": "server_name", "type": "text", "description": "Servername / Domain",
         "required": False, "default": "localhost"},
        {"name": "port", "type": "number", "description": "Listen-Port", "required": False, "default": 80},
        {"name": "upstream_port", "type": "number",
         "description": "Upstream-Port (für Reverse-Proxy)", "required": False, "default": 3000},
        {"name": "ssl", "type": "boolean", "description": "SSL/TLS aktivieren", "required": False},
        {"name": "gzip", "type": "boolean", "description": "GZIP aktivieren", "required": False},
    ],
)
def generate_nginx_conf(params: dict) -> dict:
    mode = params.get("mode", "reverse-proxy")
    server_name = params.get("server_name", "localhost")
    port = int(params.get("port", 80))
    upstream_port = int(params.get("upstream_port", 3000))
    ssl = params.get("ssl", False)
    gzip = params.get("gzip", False)

    sections = ["# nginx.conf — generated by AssetForge", ""]

    # Gzip
    if gzip:
        sections.append("""http {
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;
""")
    else:
        sections.append("http {")

    # Server block
    listen = f"    listen {port};"
    if ssl:
        listen += f"\n    listen {port} ssl;"
        listen += "\n    ssl_certificate /etc/nginx/ssl/cert.pem;"
        listen += "\n    ssl_certificate_key /etc/nginx/ssl/key.pem;"
        listen += "\n    ssl_protocols TLSv1.2 TLSv1.3;"

    sections.append(f"""    server {{
{listen}
        server_name {server_name};
""")

    if mode == "reverse-proxy":
        sections.append(f"""        location / {{
            proxy_pass http://127.0.0.1:{upstream_port};
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }}""")
    elif mode == "spa":
        sections.append("""        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }""")
    else:  # static
        sections.append("""        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ =404;
        }""")

    sections.append("    }")
    sections.append("}")

    content = "\n".join(sections) + "\n"
    out = get_output_dir() / "nginx.conf"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"nginx.conf generiert ({mode}, Port {port})"}


# ── ESLint Config ─────────────────────────────────────────

@register(
    name="eslintrc",
    category="Konfiguration",
    description="Generiert eine ESLint Flat Config (eslint.config.js)",
    parameters=[
        {"name": "framework", "type": "select", "options": ["none", "react", "vue", "next"],
         "description": "Framework", "required": False},
        {"name": "typescript", "type": "boolean", "description": "TypeScript-Support", "required": False},
        {"name": "prettier", "type": "boolean", "description": "Prettier-Integration", "required": False},
    ],
)
def generate_eslintrc(params: dict) -> dict:
    framework = params.get("framework", "none")
    ts = params.get("typescript", False)
    prettier = params.get("prettier", False)

    imports = ['import js from "@eslint/js";']
    configs = ["js.configs.recommended"]

    if ts:
        imports.append('import tseslint from "typescript-eslint";')
        configs.append("...tseslint.configs.recommended")

    if framework == "react" or framework == "next":
        imports.append('import react from "eslint-plugin-react";')
        imports.append('import reactHooks from "eslint-plugin-react-hooks";')
        configs.append('{ plugins: { react, "react-hooks": reactHooks }, settings: { react: { version: "detect" } } }')

    if framework == "vue":
        imports.append('import vue from "eslint-plugin-vue";')
        configs.append("...vue.configs['flat/recommended']")

    if prettier:
        imports.append('import prettier from "eslint-config-prettier";')
        configs.append("prettier")

    rules = []
    rules.append('    "no-unused-vars": "warn"')
    rules.append('    "no-console": "warn"')
    if ts:
        rules.append('    "@typescript-eslint/no-explicit-any": "warn"')

    content = "\n".join(imports)
    content += "\n\nexport default [\n"
    content += ",\n".join(f"  {c}" for c in configs)
    content += ",\n  {\n    rules: {\n"
    content += ",\n".join(f"      {r}" for r in rules)
    content += "\n    }\n  }\n];\n"

    out = get_output_dir() / "eslint.config.js"
    out.write_text(content, encoding="utf-8")
    features = [framework] if framework != "none" else []
    if ts: features.append("TypeScript")
    if prettier: features.append("Prettier")
    return {"files": [str(out)], "message": f"eslint.config.js generiert ({', '.join(features) or 'Basis'})"}


# ── GitHub Templates ──────────────────────────────────────

@register(
    name="github-templates",
    category="Dokumentation",
    description="Generiert GitHub Issue- und PR-Templates",
    parameters=[
        {"name": "project_name", "type": "text", "description": "Projektname", "required": True},
        {"name": "bug_report", "type": "boolean", "description": "Bug Report Template", "required": False},
        {"name": "feature_request", "type": "boolean", "description": "Feature Request Template", "required": False},
        {"name": "pull_request", "type": "boolean", "description": "Pull Request Template", "required": False},
    ],
)
def generate_github_templates(params: dict) -> dict:
    name = params.get("project_name", "Project")
    files = []

    gh_dir = get_output_dir() / ".github"
    issue_dir = gh_dir / "ISSUE_TEMPLATE"

    if params.get("bug_report", True):
        issue_dir.mkdir(parents=True, exist_ok=True)
        bug = f"""---
name: Bug Report
about: Einen Fehler melden
title: "[BUG] "
labels: bug
---

## Beschreibung
<!-- Was ist passiert? -->

## Erwartetes Verhalten
<!-- Was hätte passieren sollen? -->

## Schritte zur Reproduktion
1.
2.
3.

## Umgebung
- OS:
- Browser:
- {name} Version:

## Screenshots
<!-- Falls vorhanden -->
"""
        out = issue_dir / "bug_report.md"
        out.write_text(bug, encoding="utf-8")
        files.append(str(out))

    if params.get("feature_request", True):
        issue_dir.mkdir(parents=True, exist_ok=True)
        feature = f"""---
name: Feature Request
about: Eine neue Funktion vorschlagen
title: "[FEATURE] "
labels: enhancement
---

## Zusammenfassung
<!-- Kurze Beschreibung der gewünschten Funktion -->

## Motivation
<!-- Warum wird dieses Feature benötigt? -->

## Vorgeschlagene Lösung
<!-- Wie könnte es umgesetzt werden? -->

## Alternativen
<!-- Andere Lösungsansätze -->
"""
        out = issue_dir / "feature_request.md"
        out.write_text(feature, encoding="utf-8")
        files.append(str(out))

    if params.get("pull_request", True):
        gh_dir.mkdir(parents=True, exist_ok=True)
        pr = f"""## Beschreibung
<!-- Was wurde geändert und warum? -->

## Typ der Änderung
- [ ] Bug Fix
- [ ] Neues Feature
- [ ] Breaking Change
- [ ] Dokumentation

## Checkliste
- [ ] Code folgt den Projektrichtlinien
- [ ] Tests wurden hinzugefügt/aktualisiert
- [ ] Dokumentation wurde aktualisiert
- [ ] Alle Tests bestehen
"""
        out = gh_dir / "pull_request_template.md"
        out.write_text(pr, encoding="utf-8")
        files.append(str(out))

    templates = []
    if params.get("bug_report", True): templates.append("Bug Report")
    if params.get("feature_request", True): templates.append("Feature Request")
    if params.get("pull_request", True): templates.append("PR Template")
    return {"files": files, "message": f"GitHub Templates generiert ({', '.join(templates)})"}


# ── Tailwind Config ───────────────────────────────────────

@register(
    name="tailwind-config",
    category="Konfiguration",
    description="Generiert eine tailwind.config.js mit Theme-Anpassungen",
    parameters=[
        {"name": "content_paths", "type": "text",
         "description": "Content-Pfade (kommagetrennt)", "required": False,
         "default": "./src/**/*.{js,ts,jsx,tsx,html}"},
        {"name": "dark_mode", "type": "select", "options": ["class", "media", "selector"],
         "description": "Dark-Mode-Strategie", "required": False},
        {"name": "primary_color", "type": "color", "description": "Primärfarbe", "required": False, "default": "#3b82f6"},
        {"name": "plugins", "type": "multi-select",
         "options": ["forms", "typography", "aspect-ratio", "container-queries"],
         "description": "Plugins", "required": False},
    ],
)
def generate_tailwind_config(params: dict) -> dict:
    content = params.get("content_paths", "./src/**/*.{js,ts,jsx,tsx,html}")
    dark_mode = params.get("dark_mode", "class")
    primary = params.get("primary_color", "#3b82f6")
    plugins = params.get("plugins", [])
    if isinstance(plugins, str):
        plugins = [plugins] if plugins else []

    content_paths = [p.strip() for p in content.split(",") if p.strip()]
    content_arr = ", ".join(f'"{p}"' for p in content_paths)

    plugin_imports = []
    plugin_refs = []
    for p in plugins:
        plugin_imports.append(f'const {p} = require("@tailwindcss/plugin-{p}");')
        plugin_refs.append(f"    {p}")

    lines = []
    if plugin_imports:
        lines.extend(plugin_imports)
        lines.append("")

    lines.append("/** @type {import('tailwindcss').Config} */")
    lines.append("module.exports = {")
    lines.append(f"  content: [{content_arr}],")
    lines.append(f'  darkMode: "{dark_mode}",')
    lines.append("  theme: {")
    lines.append("    extend: {")
    lines.append("      colors: {")
    lines.append(f'        primary: "{primary}",')
    lines.append("      },")
    lines.append("    },")
    lines.append("  },")
    if plugin_refs:
        lines.append("  plugins: [")
        lines.append(",\n".join(plugin_refs))
        lines.append("  ],")
    else:
        lines.append("  plugins: [],")
    lines.append("};")

    out = get_output_dir() / "tailwind.config.js"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"files": [str(out)], "message": f"tailwind.config.js generiert ({dark_mode})"}


# ── Vite Config ───────────────────────────────────────────

@register(
    name="vite-config",
    category="Konfiguration",
    description="Generiert eine vite.config.ts für moderne Frontend-Projekte",
    parameters=[
        {"name": "framework", "type": "select", "options": ["react", "vue", "svelte", "vanilla"],
         "description": "Framework", "required": False},
        {"name": "port", "type": "number", "description": "Dev-Server Port", "required": False, "default": 5173},
        {"name": "api_proxy", "type": "text",
         "description": "API-Proxy URL (z.B. http://localhost:3000)", "required": False},
    ],
)
def generate_vite_config(params: dict) -> dict:
    framework = params.get("framework", "react")
    port = int(params.get("port", 5173))
    proxy = params.get("api_proxy", "")

    imports = ['import { defineConfig } from "vite";']
    plugins = []

    if framework == "react":
        imports.append('import react from "@vitejs/plugin-react";')
        plugins.append("react()")
    elif framework == "vue":
        imports.append('import vue from "@vitejs/plugin-vue";')
        plugins.append("vue()")
    elif framework == "svelte":
        imports.append('import { svelte } from "@sveltejs/vite-plugin-svelte";')
        plugins.append("svelte()")

    lines = imports + ["", "export default defineConfig({"]
    if plugins:
        lines.append(f"  plugins: [{', '.join(plugins)}],")

    lines.append("  server: {")
    lines.append(f"    port: {port},")
    if proxy:
        lines.append("    proxy: {")
        lines.append(f'      "/api": "{proxy}",')
        lines.append("    },")
    lines.append("  },")
    lines.append("  build: {")
    lines.append('    outDir: "dist",')
    lines.append("    sourcemap: true,")
    lines.append("  },")
    lines.append("});")

    ext = "ts"
    out = get_output_dir() / f"vite.config.{ext}"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"files": [str(out)], "message": f"vite.config.{ext} generiert ({framework}, Port {port})"}


# ── Jest Config ───────────────────────────────────────────

@register(
    name="jest-config",
    category="Konfiguration",
    description="Generiert eine jest.config.js für Unit-Tests",
    parameters=[
        {"name": "typescript", "type": "boolean", "description": "TypeScript-Support (ts-jest)", "required": False},
        {"name": "framework", "type": "select", "options": ["none", "react", "vue", "node"],
         "description": "Framework", "required": False},
        {"name": "coverage", "type": "boolean", "description": "Code-Coverage aktivieren", "required": False},
    ],
)
def generate_jest_config(params: dict) -> dict:
    ts = params.get("typescript", False)
    framework = params.get("framework", "none")
    coverage = params.get("coverage", False)

    config = {}

    if ts:
        config["preset"] = "ts-jest"
    if framework in ("react", "vue"):
        config["testEnvironment"] = "jsdom"
    else:
        config["testEnvironment"] = "node"

    config["testMatch"] = ["**/__tests__/**/*.[jt]s?(x)", "**/?(*.)+(spec|test).[jt]s?(x)"]
    config["moduleFileExtensions"] = ["ts", "tsx", "js", "jsx", "json"] if ts else ["js", "jsx", "json"]

    if framework == "react":
        config["setupFilesAfterSetup"] = ["<rootDir>/src/setupTests.ts" if ts else "<rootDir>/src/setupTests.js"]
        config["moduleNameMapper"] = {"\\\\.(css|less|scss)$": "identity-obj-proxy"}

    if coverage:
        config["collectCoverage"] = True
        config["coverageDirectory"] = "coverage"
        config["coverageReporters"] = ["text", "lcov", "clover"]
        config["collectCoverageFrom"] = ["src/**/*.{js,jsx,ts,tsx}", "!src/**/*.d.ts"]

    content = "/** @type {import('jest').Config} */\nmodule.exports = " + json.dumps(config, indent=2) + ";\n"
    out = get_output_dir() / "jest.config.js"
    out.write_text(content, encoding="utf-8")
    features = []
    if ts: features.append("TypeScript")
    if framework != "none": features.append(framework)
    if coverage: features.append("Coverage")
    return {"files": [str(out)], "message": f"jest.config.js generiert ({', '.join(features) or 'Basis'})"}


# ── PWA Manifest ──────────────────────────────────────────

@register(
    name="pwa-manifest",
    category="Konfiguration",
    description="Generiert ein manifest.json für Progressive Web Apps",
    parameters=[
        {"name": "name", "type": "text", "description": "App-Name", "required": True},
        {"name": "short_name", "type": "text", "description": "Kurzname (max 12 Zeichen)", "required": False},
        {"name": "description", "type": "text", "description": "App-Beschreibung", "required": False},
        {"name": "theme_color", "type": "color", "description": "Theme-Farbe", "required": False, "default": "#e94560"},
        {"name": "bg_color", "type": "color", "description": "Hintergrundfarbe", "required": False, "default": "#0a0a0f"},
        {"name": "display", "type": "select", "options": ["standalone", "fullscreen", "minimal-ui", "browser"],
         "description": "Display-Modus", "required": False},
        {"name": "start_url", "type": "text", "description": "Start-URL", "required": False, "default": "/"},
    ],
)
def generate_pwa_manifest(params: dict) -> dict:
    name = params.get("name", "My App")
    short = params.get("short_name", name[:12])
    desc = params.get("description", "")
    theme = params.get("theme_color", "#e94560")
    bg = params.get("bg_color", "#0a0a0f")
    display = params.get("display", "standalone")
    start = params.get("start_url", "/")

    manifest = {
        "name": name,
        "short_name": short,
        "description": desc,
        "start_url": start,
        "display": display,
        "theme_color": theme,
        "background_color": bg,
        "icons": [
            {"src": f"/icons/icon-{s}x{s}.png", "sizes": f"{s}x{s}", "type": "image/png"}
            for s in [72, 96, 128, 144, 192, 384, 512]
        ],
    }

    content = json.dumps(manifest, indent=2, ensure_ascii=False)
    out = get_output_dir() / "manifest.json"
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"manifest.json generiert ({display})"}


# ── Vitest Config ─────────────────────────────────────────

@register(
    name="vitest-config",
    category="Konfiguration",
    description="Generiert eine vitest.config.ts für schnelle Unit-Tests",
    parameters=[
        {"name": "framework", "type": "select", "options": ["react", "vue", "svelte", "vanilla"],
         "description": "Framework", "required": False},
        {"name": "coverage", "type": "boolean", "description": "Coverage mit @vitest/coverage-v8", "required": False},
        {"name": "globals", "type": "boolean", "description": "Globale Test-APIs (describe, it, expect)", "required": False},
    ],
)
def generate_vitest_config(params: dict) -> dict:
    framework = params.get("framework", "vanilla")
    coverage = params.get("coverage", False)
    globals_api = params.get("globals", True)

    imports = ['import { defineConfig } from "vitest/config";']
    plugins = []

    if framework == "react":
        imports.append('import react from "@vitejs/plugin-react";')
        plugins.append("react()")
    elif framework == "vue":
        imports.append('import vue from "@vitejs/plugin-vue";')
        plugins.append("vue()")

    lines = imports + ["", "export default defineConfig({"]
    if plugins:
        lines.append(f"  plugins: [{', '.join(plugins)}],")

    lines.append("  test: {")
    if globals_api:
        lines.append("    globals: true,")
    if framework in ("react", "vue", "svelte"):
        lines.append('    environment: "jsdom",')
    else:
        lines.append('    environment: "node",')

    lines.append('    include: ["src/**/*.{test,spec}.{js,ts,jsx,tsx}"],')

    if coverage:
        lines.append("    coverage: {")
        lines.append('      provider: "v8",')
        lines.append('      reporter: ["text", "lcov"],')
        lines.append("    },")

    lines.append("  },")
    lines.append("});")

    out = get_output_dir() / "vitest.config.ts"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    features = []
    if framework != "vanilla": features.append(framework)
    if coverage: features.append("Coverage")
    if globals_api: features.append("Globals")
    return {"files": [str(out)], "message": f"vitest.config.ts generiert ({', '.join(features) or 'Basis'})"}


# ── .env Validator ────────────────────────────────────────

@register(
    name="env-validator",
    category="Konfiguration",
    description="Generiert ein .env.example und ein Validierungs-Script",
    parameters=[
        {"name": "variables", "type": "text",
         "description": "Variablen (kommagetrennt, z.B. DATABASE_URL,API_KEY,PORT)",
         "required": True},
        {"name": "language", "type": "select", "options": ["node", "python"],
         "description": "Script-Sprache", "required": False},
    ],
)
def generate_env_validator(params: dict) -> dict:
    vars_str = params.get("variables", "DATABASE_URL,API_KEY,PORT")
    lang = params.get("language", "node")
    variables = [v.strip() for v in vars_str.split(",") if v.strip()]
    files = []

    # .env.example
    example_lines = ["# .env.example — generated by AssetForge", "# Kopiere diese Datei nach .env und fülle die Werte aus", ""]
    for var in variables:
        example_lines.append(f"{var}=")
    example_out = get_output_dir() / ".env.example"
    example_out.write_text("\n".join(example_lines) + "\n", encoding="utf-8")
    files.append(str(example_out))

    # Validation script
    if lang == "node":
        checks = "\n".join(f'  "{var}",' for var in variables)
        script = f"""// validate-env.js — generated by AssetForge
const required = [
{checks}
];

const missing = required.filter(key => !process.env[key]);
if (missing.length > 0) {{
  console.error("Missing environment variables:");
  missing.forEach(key => console.error(`  - ${{key}}`));
  process.exit(1);
}}
console.log("All environment variables are set.");
"""
        out = get_output_dir() / "validate-env.js"
    else:
        checks = "\n".join(f'    "{var}",' for var in variables)
        script = f'''"""validate_env.py — generated by AssetForge"""
import os
import sys

REQUIRED = [
{checks}
]

missing = [key for key in REQUIRED if not os.environ.get(key)]
if missing:
    print("Missing environment variables:", file=sys.stderr)
    for key in missing:
        print(f"  - {{key}}", file=sys.stderr)
    sys.exit(1)
print("All environment variables are set.")
'''
        out = get_output_dir() / "validate_env.py"

    out.write_text(script, encoding="utf-8")
    files.append(str(out))
    return {"files": files, "message": f".env.example + Validator generiert ({len(variables)} Variablen, {lang})"}


# ── Commitlint Config ─────────────────────────────────────

@register(
    name="commitlint-config",
    category="Konfiguration",
    description="Generiert commitlint + husky Setup für konventionelle Commits",
    parameters=[
        {"name": "preset", "type": "select",
         "options": ["conventional", "angular", "atom"],
         "description": "Commit-Konvention", "required": False},
        {"name": "husky", "type": "boolean", "description": "Husky Git-Hooks einrichten", "required": False},
    ],
)
def generate_commitlint_config(params: dict) -> dict:
    preset = params.get("preset", "conventional")
    husky = params.get("husky", True)
    files = []

    presets_map = {
        "conventional": "@commitlint/config-conventional",
        "angular": "@commitlint/config-angular",
        "atom": "@commitlint/config-atom",
    }

    config = {
        "extends": [presets_map.get(preset, presets_map["conventional"])],
        "rules": {
            "type-enum": [2, "always", [
                "feat", "fix", "docs", "style", "refactor",
                "perf", "test", "build", "ci", "chore", "revert",
            ]],
            "subject-case": [2, "never", ["start-case", "pascal-case", "upper-case"]],
            "subject-max-length": [2, "always", 72],
        },
    }

    out = get_output_dir() / "commitlint.config.js"
    out.write_text(f"module.exports = {json.dumps(config, indent=2)};\n", encoding="utf-8")
    files.append(str(out))

    if husky:
        husky_dir = get_output_dir() / ".husky"
        husky_dir.mkdir(exist_ok=True)
        commit_msg = husky_dir / "commit-msg"
        commit_msg.write_text('#!/usr/bin/env sh\n. "$(dirname -- "$0")/_/husky.sh"\n\nnpx --no -- commitlint --edit ${1}\n', encoding="utf-8")
        files.append(str(commit_msg))

    return {"files": files, "message": f"commitlint ({preset}) + {'Husky' if husky else 'ohne Husky'} generiert"}


# ── Renovate Config ───────────────────────────────────────

@register(
    name="renovate-config",
    category="Konfiguration",
    description="Generiert eine renovate.json für automatische Dependency-Updates",
    parameters=[
        {"name": "schedule", "type": "select",
         "options": ["weekly", "monthly", "daily"],
         "description": "Update-Zeitplan", "required": False},
        {"name": "automerge", "type": "boolean", "description": "Minor/Patch automatisch mergen", "required": False},
        {"name": "labels", "type": "text", "description": "PR-Labels (kommagetrennt)", "required": False, "default": "dependencies"},
    ],
)
def generate_renovate_config(params: dict) -> dict:
    schedule = params.get("schedule", "weekly")
    automerge = params.get("automerge", False)
    labels_str = params.get("labels", "dependencies")
    labels = [l.strip() for l in labels_str.split(",") if l.strip()]

    schedule_map = {
        "weekly": ["every weekend"],
        "monthly": ["before 5am on the first day of the month"],
        "daily": ["every weekday"],
    }

    config = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "extends": ["config:recommended"],
        "schedule": schedule_map.get(schedule, schedule_map["weekly"]),
        "labels": labels,
        "packageRules": [],
    }

    if automerge:
        config["packageRules"].append({
            "matchUpdateTypes": ["minor", "patch"],
            "automerge": True,
        })

    config["packageRules"].append({
        "matchUpdateTypes": ["major"],
        "labels": labels + ["breaking"],
    })

    out = get_output_dir() / "renovate.json"
    out.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    features = [schedule]
    if automerge: features.append("Automerge")
    return {"files": [str(out)], "message": f"renovate.json generiert ({', '.join(features)})"}


# ── Stylelint Config ─────────────────────────────────────

@register(
    name="stylelint-config",
    category="Konfiguration",
    description="Generiert eine .stylelintrc.json für CSS/SCSS Linting",
    parameters=[
        {"name": "preprocessor", "type": "select", "options": ["css", "scss", "less"],
         "description": "CSS-Preprocessor", "required": False},
        {"name": "order", "type": "boolean", "description": "Property-Order Plugin", "required": False},
        {"name": "prettier", "type": "boolean", "description": "Prettier-Integration", "required": False},
    ],
)
def generate_stylelint_config(params: dict) -> dict:
    preprocessor = params.get("preprocessor", "css")
    order = params.get("order", False)
    prettier = params.get("prettier", False)

    extends = ["stylelint-config-standard"]
    plugins = []

    if preprocessor == "scss":
        extends.append("stylelint-config-standard-scss")
    elif preprocessor == "less":
        extends.append("stylelint-config-standard-less")

    if order:
        plugins.append("stylelint-order")
        extends.append("stylelint-config-recess-order")

    if prettier:
        extends.append("stylelint-config-prettier")

    config = {
        "extends": extends,
    }
    if plugins:
        config["plugins"] = plugins

    config["rules"] = {
        "selector-class-pattern": None,
        "no-descending-specificity": None,
        "color-function-notation": "modern",
    }

    if preprocessor == "scss":
        config["rules"]["scss/dollar-variable-pattern"] = "^[a-z][a-z0-9-]*$"

    content = json.dumps(config, indent=2, ensure_ascii=False)
    out = get_output_dir() / ".stylelintrc.json"
    out.write_text(content + "\n", encoding="utf-8")

    # .stylelintignore
    ignore_lines = ["node_modules/", "dist/", "build/", "coverage/", "*.min.css"]
    ignore_out = get_output_dir() / ".stylelintignore"
    ignore_out.write_text("\n".join(ignore_lines) + "\n", encoding="utf-8")

    features = [preprocessor]
    if order: features.append("Order")
    if prettier: features.append("Prettier")
    return {"files": [str(out), str(ignore_out)], "message": f"Stylelint generiert ({', '.join(features)})"}


# ── Babel Config ─────────────────────────────────────────

@register(
    name="babel-config",
    category="Konfiguration",
    description="Generiert eine babel.config.json für JavaScript/TypeScript Transpilation",
    parameters=[
        {"name": "framework", "type": "select", "options": ["none", "react", "vue"],
         "description": "Framework", "required": False},
        {"name": "typescript", "type": "boolean", "description": "TypeScript-Support", "required": False},
        {"name": "targets", "type": "select", "options": ["modern", "legacy", "node"],
         "description": "Ziel-Umgebung", "required": False},
        {"name": "modules", "type": "select", "options": ["auto", "commonjs", "false"],
         "description": "Modul-System", "required": False},
    ],
)
def generate_babel_config(params: dict) -> dict:
    framework = params.get("framework", "none")
    ts = params.get("typescript", False)
    targets = params.get("targets", "modern")
    modules = params.get("modules", "auto")

    targets_map = {
        "modern": "> 0.5%, last 2 versions, not dead",
        "legacy": "> 0.2%, last 4 versions, ie 11",
        "node": "current",
    }

    presets = [
        ["@babel/preset-env", {
            "targets": {"node": "current"} if targets == "node" else targets_map.get(targets, targets_map["modern"]),
            "modules": False if modules == "false" else modules,
            "useBuiltIns": "usage",
            "corejs": 3,
        }]
    ]

    if ts:
        presets.append("@babel/preset-typescript")

    if framework == "react":
        presets.append(["@babel/preset-react", {"runtime": "automatic"}])

    babel_plugins = []
    if framework != "none":
        babel_plugins.append("@babel/plugin-proposal-optional-chaining")

    config = {"presets": presets}
    if babel_plugins:
        config["plugins"] = babel_plugins

    content = json.dumps(config, indent=2, ensure_ascii=False)
    out = get_output_dir() / "babel.config.json"
    out.write_text(content + "\n", encoding="utf-8")
    features = [targets]
    if ts: features.append("TypeScript")
    if framework != "none": features.append(framework)
    return {"files": [str(out)], "message": f"babel.config.json generiert ({', '.join(features)})"}


# ── Webpack Config ───────────────────────────────────────

@register(
    name="webpack-config",
    category="Konfiguration",
    description="Generiert eine webpack.config.js für Bundle-basierte Projekte",
    parameters=[
        {"name": "framework", "type": "select", "options": ["vanilla", "react", "vue"],
         "description": "Framework", "required": False},
        {"name": "typescript", "type": "boolean", "description": "TypeScript-Support", "required": False},
        {"name": "dev_server", "type": "boolean", "description": "Dev-Server konfigurieren", "required": False},
        {"name": "port", "type": "number", "description": "Dev-Server Port", "required": False, "default": 8080},
        {"name": "css_modules", "type": "boolean", "description": "CSS Modules aktivieren", "required": False},
    ],
)
def generate_webpack_config(params: dict) -> dict:
    framework = params.get("framework", "vanilla")
    ts = params.get("typescript", False)
    dev_server = params.get("dev_server", True)
    port = int(params.get("port", 8080))
    css_modules = params.get("css_modules", False)

    ext = "tsx" if ts and framework == "react" else ("ts" if ts else "js")
    resolve_ext = [".ts", ".tsx", ".js", ".jsx"] if ts else [".js", ".jsx"]

    lines = [
        'const path = require("path");',
        'const HtmlWebpackPlugin = require("html-webpack-plugin");',
    ]
    if framework == "vue":
        lines.append('const { VueLoaderPlugin } = require("vue-loader");')

    lines.extend([
        "",
        "module.exports = {",
        '  mode: process.env.NODE_ENV || "development",',
        f'  entry: "./src/index.{ext}",',
        "  output: {",
        '    path: path.resolve(__dirname, "dist"),',
        '    filename: "[name].[contenthash].js",',
        "    clean: true,",
        "  },",
        "  resolve: {",
        f"    extensions: {json.dumps(resolve_ext)},",
        "  },",
        "  module: {",
        "    rules: [",
    ])

    # JS/TS loader
    if ts:
        lines.append("      {")
        lines.append("        test: /\\.tsx?$/,")
        lines.append('        use: "ts-loader",')
        lines.append("        exclude: /node_modules/,")
        lines.append("      },")
    else:
        lines.append("      {")
        lines.append("        test: /\\.jsx?$/,")
        lines.append('        use: "babel-loader",')
        lines.append("        exclude: /node_modules/,")
        lines.append("      },")

    # CSS loader
    css_use = '"style-loader"'
    if css_modules:
        css_use_arr = ['"style-loader"', '{ loader: "css-loader", options: { modules: true } }']
    else:
        css_use_arr = ['"style-loader"', '"css-loader"']
    lines.append("      {")
    lines.append("        test: /\\.css$/,")
    lines.append(f"        use: [{', '.join(css_use_arr)}],")
    lines.append("      },")

    # Vue loader
    if framework == "vue":
        lines.append("      {")
        lines.append("        test: /\\.vue$/,")
        lines.append('        use: "vue-loader",')
        lines.append("      },")

    # Asset loader
    lines.append("      {")
    lines.append("        test: /\\.(png|jpe?g|gif|svg|woff2?|eot|ttf)$/,")
    lines.append('        type: "asset/resource",')
    lines.append("      },")

    lines.extend([
        "    ],",
        "  },",
        "  plugins: [",
        "    new HtmlWebpackPlugin({",
        '      template: "./src/index.html",',
        "    }),",
    ])
    if framework == "vue":
        lines.append("    new VueLoaderPlugin(),")
    lines.append("  ],")

    if dev_server:
        lines.extend([
            "  devServer: {",
            f"    port: {port},",
            "    hot: true,",
            "    open: true,",
            '    historyApiFallback: true,',
            "  },",
        ])

    lines.append("};")

    out = get_output_dir() / "webpack.config.js"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    features = [framework]
    if ts: features.append("TypeScript")
    if dev_server: features.append(f"DevServer:{port}")
    if css_modules: features.append("CSS Modules")
    return {"files": [str(out)], "message": f"webpack.config.js generiert ({', '.join(features)})"}


# ── Gitattributes ────────────────────────────────────────

@register(
    name="gitattributes",
    category="Konfiguration",
    description="Generiert eine .gitattributes für konsistente Line-Endings und Diff-Verhalten",
    parameters=[
        {"name": "stacks", "type": "multi-select",
         "options": ["general", "web", "python", "java", "go", "unity", "docs"],
         "description": "Tech-Stack(s)", "required": False},
        {"name": "lfs", "type": "multi-select",
         "options": ["png", "jpg", "gif", "psd", "zip", "pdf", "mp4", "mp3"],
         "description": "Git LFS Dateitypen", "required": False},
    ],
)
def generate_gitattributes(params: dict) -> dict:
    stacks = params.get("stacks", ["general"])
    lfs = params.get("lfs", [])
    if isinstance(stacks, str):
        stacks = [stacks] if stacks else ["general"]
    if isinstance(lfs, str):
        lfs = [lfs] if lfs else []

    lines = ["# .gitattributes — generated by AssetForge", ""]

    # Auto-detect text files and normalize line endings
    lines.extend([
        "# Auto-detect text files and normalize line endings",
        "* text=auto",
        "",
    ])

    stack_rules = {
        "general": [
            "# Common files",
            "*.md text diff=markdown",
            "*.txt text",
            "*.csv text",
            "*.json text",
            "*.yaml text",
            "*.yml text",
            "*.xml text",
            "*.toml text",
            "*.ini text",
            "*.cfg text",
            "*.conf text",
            "*.sh text eol=lf",
            "*.bat text eol=crlf",
            "Makefile text eol=lf",
            "LICENSE text",
        ],
        "web": [
            "# Web files",
            "*.html text diff=html",
            "*.css text diff=css",
            "*.js text",
            "*.jsx text",
            "*.ts text",
            "*.tsx text",
            "*.vue text",
            "*.svelte text",
            "*.scss text diff=css",
            "*.less text diff=css",
            "*.svg text",
            "*.map text",
        ],
        "python": [
            "# Python files",
            "*.py text diff=python",
            "*.pyi text diff=python",
            "*.pyx text diff=python",
            "*.ipynb text",
            "requirements*.txt text",
            "Pipfile text",
            "pyproject.toml text",
        ],
        "java": [
            "# Java files",
            "*.java text diff=java",
            "*.kt text diff=kotlin",
            "*.gradle text diff=java",
            "*.properties text",
            "*.jar binary",
            "*.war binary",
            "*.class binary",
            "gradlew text eol=lf",
            "gradlew.bat text eol=crlf",
            "mvnw text eol=lf",
            "mvnw.cmd text eol=crlf",
        ],
        "go": [
            "# Go files",
            "*.go text diff=golang",
            "go.sum text",
            "go.mod text",
        ],
        "unity": [
            "# Unity files",
            "*.unity text merge=unityyamlmerge",
            "*.prefab text merge=unityyamlmerge",
            "*.asset text merge=unityyamlmerge",
            "*.mat text merge=unityyamlmerge",
            "*.meta text",
            "*.controller text",
            "*.anim text",
            "*.cs text diff=csharp",
            "*.cginc text",
            "*.shader text",
            "*.dll binary",
            "*.exe binary",
        ],
        "docs": [
            "# Documentation",
            "*.md text diff=markdown",
            "*.mdx text diff=markdown",
            "*.rst text",
            "*.adoc text",
            "*.tex text diff=tex",
        ],
    }

    for stack in stacks:
        if stack in stack_rules:
            lines.extend(stack_rules[stack])
            lines.append("")

    # Binary files (always)
    lines.extend([
        "# Binary files",
        "*.png binary",
        "*.jpg binary",
        "*.jpeg binary",
        "*.gif binary",
        "*.ico binary",
        "*.webp binary",
        "*.woff binary",
        "*.woff2 binary",
        "*.ttf binary",
        "*.eot binary",
        "*.zip binary",
        "*.gz binary",
        "*.tar binary",
        "*.pdf binary",
    ])

    # Git LFS
    if lfs:
        lines.extend(["", "# Git LFS"])
        for ext in lfs:
            lines.append(f"*.{ext} filter=lfs diff=lfs merge=lfs -text")

    out = get_output_dir() / ".gitattributes"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"files": [str(out)], "message": f".gitattributes generiert ({', '.join(stacks)}" + (f", LFS: {', '.join(lfs)}" if lfs else "") + ")"}


# ── Testdaten Generator ──────────────────────────────────

@register(
    name="testdata",
    category="Datenbank",
    description="Generiert realistische Testdaten als JSON oder CSV",
    parameters=[
        {"name": "format", "type": "select", "options": ["json", "csv"],
         "description": "Ausgabeformat", "required": False},
        {"name": "schema", "type": "select",
         "options": ["users", "products", "orders", "blog-posts", "contacts", "events"],
         "description": "Daten-Schema", "required": True},
        {"name": "count", "type": "number", "description": "Anzahl Datensätze", "required": False, "default": 10},
        {"name": "locale", "type": "select", "options": ["de", "en"],
         "description": "Sprache der Daten", "required": False},
    ],
)
def generate_testdata(params: dict) -> dict:
    import random
    import csv
    import io

    fmt = params.get("format", "json")
    schema = params.get("schema", "users")
    count = min(int(params.get("count", 10)), 100)
    locale = params.get("locale", "de")

    de_first = ["Max", "Anna", "Lukas", "Sophie", "Felix", "Emma", "Leon", "Mia", "Paul", "Lena",
                "Tim", "Laura", "Jan", "Julia", "Tom", "Sarah", "Niklas", "Marie", "David", "Lisa"]
    de_last = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
               "Schulz", "Hoffmann", "Koch", "Richter", "Wolf", "Klein", "Schröder", "Braun"]
    en_first = ["James", "Emma", "Oliver", "Sophia", "William", "Ava", "Benjamin", "Isabella",
                "Lucas", "Mia", "Henry", "Charlotte", "Alexander", "Amelia", "Daniel", "Harper"]
    en_last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
               "Rodriguez", "Martinez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson"]

    first_names = de_first if locale == "de" else en_first
    last_names = de_last if locale == "de" else en_last

    de_cities = ["Berlin", "München", "Hamburg", "Köln", "Frankfurt", "Stuttgart", "Düsseldorf",
                 "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden", "Hannover", "Nürnberg"]
    en_cities = ["New York", "London", "San Francisco", "Chicago", "Austin", "Seattle",
                 "Denver", "Boston", "Portland", "Miami", "Toronto", "Amsterdam"]
    cities = de_cities if locale == "de" else en_cities

    domains = ["gmail.com", "outlook.com", "yahoo.com", "web.de", "gmx.de", "company.com"]
    product_names = ["Widget Pro", "Gadget X", "Alpha Sensor", "NeoBoard", "SmartClip", "DataPulse",
                     "CloudSync", "PixelFrame", "TurboKit", "EcoVolt", "ByteBox", "FlexHub",
                     "LogicCore", "StreamLink", "QuickPad", "PowerNode"]
    categories = ["Elektronik", "Software", "Hardware", "Zubehör", "Büro", "Gaming"] if locale == "de" \
        else ["Electronics", "Software", "Hardware", "Accessories", "Office", "Gaming"]
    statuses_order = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    tags = ["tech", "news", "tutorial", "review", "opinion", "guide", "update", "release"]

    records = []
    for i in range(count):
        first = random.choice(first_names)
        last = random.choice(last_names)
        email = f"{first.lower()}.{last.lower()}@{random.choice(domains)}".replace("ü", "ue").replace("ö", "oe").replace("ä", "ae")

        if schema == "users":
            records.append({
                "id": i + 1,
                "first_name": first,
                "last_name": last,
                "email": email,
                "age": random.randint(18, 65),
                "city": random.choice(cities),
                "role": random.choice(["admin", "user", "editor", "viewer"]),
                "active": random.choice([True, True, True, False]),
                "created_at": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(8,20):02d}:{random.randint(0,59):02d}:00Z",
            })
        elif schema == "products":
            records.append({
                "id": i + 1,
                "name": f"{random.choice(product_names)} {random.choice(['S', 'M', 'L', 'XL', 'Mini', 'Max', 'Pro', 'Lite'])}",
                "price": round(random.uniform(4.99, 499.99), 2),
                "currency": "EUR" if locale == "de" else "USD",
                "category": random.choice(categories),
                "stock": random.randint(0, 500),
                "sku": f"SKU-{random.randint(10000, 99999)}",
                "rating": round(random.uniform(1.0, 5.0), 1),
                "available": random.choice([True, True, True, False]),
            })
        elif schema == "orders":
            records.append({
                "id": f"ORD-{random.randint(100000, 999999)}",
                "customer": f"{first} {last}",
                "email": email,
                "total": round(random.uniform(9.99, 999.99), 2),
                "currency": "EUR" if locale == "de" else "USD",
                "items": random.randint(1, 8),
                "status": random.choice(statuses_order),
                "payment_method": random.choice(["credit_card", "paypal", "bank_transfer", "klarna"]),
                "ordered_at": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            })
        elif schema == "blog-posts":
            titles_de = ["Wie man", "Warum", "Die besten", "Einführung in", "Guide zu", "Alles über"]
            titles_en = ["How to", "Why", "Top 10", "Introduction to", "Guide to", "Everything about"]
            topics = ["Machine Learning", "Cloud Computing", "DevOps", "React", "Python", "Docker",
                      "Kubernetes", "TypeScript", "GraphQL", "Microservices"]
            title_prefix = random.choice(titles_de if locale == "de" else titles_en)
            records.append({
                "id": i + 1,
                "title": f"{title_prefix} {random.choice(topics)}",
                "slug": f"post-{i+1}-{random.choice(topics).lower().replace(' ', '-')}",
                "author": f"{first} {last}",
                "tags": random.sample(tags, k=random.randint(1, 3)),
                "views": random.randint(10, 50000),
                "likes": random.randint(0, 500),
                "published": random.choice([True, True, False]),
                "published_at": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            })
        elif schema == "contacts":
            records.append({
                "id": i + 1,
                "name": f"{first} {last}",
                "email": email,
                "phone": f"+49 {random.randint(150, 179)} {random.randint(1000000, 9999999)}" if locale == "de"
                    else f"+1 {random.randint(200, 999)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
                "company": random.choice(["TechCorp", "DataFlow", "CloudBase", "NetSolutions", "AppWorks", "DevHouse", "CodeLab", "BitForge"]),
                "position": random.choice(["CEO", "CTO", "Developer", "Designer", "PM", "Sales", "Marketing", "HR"]),
                "city": random.choice(cities),
            })
        elif schema == "events":
            event_names = ["Workshop", "Meetup", "Konferenz", "Webinar", "Hackathon", "Summit", "Bootcamp"] if locale == "de" \
                else ["Workshop", "Meetup", "Conference", "Webinar", "Hackathon", "Summit", "Bootcamp"]
            topics_short = ["AI", "DevOps", "Frontend", "Cloud", "Security", "Data", "Mobile", "Web"]
            records.append({
                "id": i + 1,
                "name": f"{random.choice(topics_short)} {random.choice(event_names)} 2025",
                "date": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "time": f"{random.randint(9,18):02d}:00",
                "location": random.choice(cities),
                "capacity": random.choice([20, 50, 100, 200, 500]),
                "registered": random.randint(5, 200),
                "online": random.choice([True, False]),
                "price": round(random.uniform(0, 149.99), 2),
            })

    if fmt == "csv":
        if not records:
            content = ""
        else:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            for r in records:
                # Flatten lists for CSV
                flat = {k: (", ".join(v) if isinstance(v, list) else v) for k, v in r.items()}
                writer.writerow(flat)
            content = output.getvalue()
        filename = f"testdata-{schema}.csv"
    else:
        content = json.dumps(records, indent=2, ensure_ascii=False)
        filename = f"testdata-{schema}.json"

    out = get_output_dir() / filename
    out.write_text(content, encoding="utf-8")
    return {"files": [str(out)], "message": f"{count} {schema}-Datensätze generiert ({fmt.upper()}, {locale.upper()})"}


# ── API Route Generator ──────────────────────────────────

@register(
    name="api-routes",
    category="Konfiguration",
    description="Generiert API-Route Boilerplate für Express, Fastify oder FastAPI",
    parameters=[
        {"name": "framework", "type": "select",
         "options": ["express", "fastify", "fastapi"],
         "description": "Backend-Framework", "required": True},
        {"name": "resource", "type": "text",
         "description": "Resource-Name (z.B. users, products, orders)", "required": True},
        {"name": "operations", "type": "multi-select",
         "options": ["list", "get", "create", "update", "delete"],
         "description": "CRUD-Operationen", "required": False},
        {"name": "auth", "type": "boolean", "description": "Auth-Middleware inkludieren", "required": False},
        {"name": "validation", "type": "boolean", "description": "Input-Validierung", "required": False},
    ],
)
def generate_api_routes(params: dict) -> dict:
    framework = params.get("framework", "express")
    resource = params.get("resource", "items").lower().strip()
    operations = params.get("operations", ["list", "get", "create", "update", "delete"])
    auth = params.get("auth", False)
    validation = params.get("validation", False)
    if isinstance(operations, str):
        operations = [operations] if operations else ["list", "get", "create", "update", "delete"]

    singular = resource.rstrip("s") if resource.endswith("s") and len(resource) > 2 else resource
    capitalized = singular.capitalize()

    if framework == "express":
        lines = [
            f'// {resource} routes — generated by AssetForge',
            f'const express = require("express");',
            f'const router = express.Router();',
        ]
        if auth:
            lines.append('const { authenticate } = require("../middleware/auth");')
        if validation:
            lines.append('const { validateBody } = require("../middleware/validate");')
        lines.append("")

        middleware = "authenticate, " if auth else ""

        if "list" in operations:
            lines.extend([
                f'// GET /{resource} — List all {resource}',
                f'router.get("/", {middleware}async (req, res) => {{',
                '  try {',
                f'    // const {resource} = await {capitalized}.find(req.query);',
                f'    res.json({{ {resource}: [], total: 0 }});',
                '  } catch (err) {',
                '    res.status(500).json({ error: err.message });',
                '  }',
                '});', '',
            ])
        if "get" in operations:
            lines.extend([
                f'// GET /{resource}/:id — Get {singular} by ID',
                f'router.get("/:id", {middleware}async (req, res) => {{',
                '  try {',
                f'    // const {singular} = await {capitalized}.findById(req.params.id);',
                f'    // if (!{singular}) return res.status(404).json({{ error: "Not found" }});',
                f'    res.json({{ {singular}: {{}} }});',
                '  } catch (err) {',
                '    res.status(500).json({ error: err.message });',
                '  }',
                '});', '',
            ])
        if "create" in operations:
            val_mw = "validateBody, " if validation else ""
            lines.extend([
                f'// POST /{resource} — Create {singular}',
                f'router.post("/", {middleware}{val_mw}async (req, res) => {{',
                '  try {',
                f'    // const {singular} = await {capitalized}.create(req.body);',
                f'    res.status(201).json({{ {singular}: req.body }});',
                '  } catch (err) {',
                '    res.status(400).json({ error: err.message });',
                '  }',
                '});', '',
            ])
        if "update" in operations:
            val_mw = "validateBody, " if validation else ""
            lines.extend([
                f'// PUT /{resource}/:id — Update {singular}',
                f'router.put("/:id", {middleware}{val_mw}async (req, res) => {{',
                '  try {',
                f'    // const {singular} = await {capitalized}.findByIdAndUpdate(req.params.id, req.body);',
                f'    res.json({{ {singular}: req.body }});',
                '  } catch (err) {',
                '    res.status(400).json({ error: err.message });',
                '  }',
                '});', '',
            ])
        if "delete" in operations:
            lines.extend([
                f'// DELETE /{resource}/:id — Delete {singular}',
                f'router.delete("/:id", {middleware}async (req, res) => {{',
                '  try {',
                f'    // await {capitalized}.findByIdAndDelete(req.params.id);',
                '    res.status(204).send();',
                '  } catch (err) {',
                '    res.status(500).json({ error: err.message });',
                '  }',
                '});', '',
            ])

        lines.append('module.exports = router;')
        filename = f"routes/{resource}.js"

    elif framework == "fastify":
        lines = [
            f'// {resource} routes — generated by AssetForge',
            f'"use strict";',
            '',
            f'async function {resource}Routes(fastify, options) {{',
        ]
        if auth:
            lines.append('  fastify.addHook("onRequest", fastify.authenticate);')
            lines.append('')

        if "list" in operations:
            lines.extend([
                f'  fastify.get("/{resource}", async (request, reply) => {{',
                f'    // const {resource} = await fastify.db.{resource}.find(request.query);',
                f'    return {{ {resource}: [], total: 0 }};',
                '  });', '',
            ])
        if "get" in operations:
            schema_str = ""
            if validation:
                schema_str = f', {{ schema: {{ params: {{ type: "object", properties: {{ id: {{ type: "string" }} }}, required: ["id"] }} }} }}'
            lines.extend([
                f'  fastify.get("/{resource}/:id"{schema_str}, async (request, reply) => {{',
                f'    const {{ id }} = request.params;',
                f'    // const {singular} = await fastify.db.{resource}.findById(id);',
                f'    return {{ {singular}: {{}} }};',
                '  });', '',
            ])
        if "create" in operations:
            lines.extend([
                f'  fastify.post("/{resource}", async (request, reply) => {{',
                f'    // const {singular} = await fastify.db.{resource}.create(request.body);',
                f'    reply.code(201);',
                f'    return {{ {singular}: request.body }};',
                '  });', '',
            ])
        if "update" in operations:
            lines.extend([
                f'  fastify.put("/{resource}/:id", async (request, reply) => {{',
                f'    const {{ id }} = request.params;',
                f'    // const {singular} = await fastify.db.{resource}.update(id, request.body);',
                f'    return {{ {singular}: request.body }};',
                '  });', '',
            ])
        if "delete" in operations:
            lines.extend([
                f'  fastify.delete("/{resource}/:id", async (request, reply) => {{',
                f'    const {{ id }} = request.params;',
                f'    // await fastify.db.{resource}.delete(id);',
                '    reply.code(204).send();',
                '  });', '',
            ])

        lines.extend(['}', '', f'module.exports = {resource}Routes;'])
        filename = f"routes/{resource}.js"

    else:  # fastapi
        lines = [
            f'"""API routes for {resource} — generated by AssetForge."""',
            '',
            'from fastapi import APIRouter, HTTPException',
        ]
        if auth:
            lines.append('from fastapi import Depends')
            lines.append('# from app.auth import get_current_user')
        if validation:
            lines.append('from pydantic import BaseModel')
            lines.extend([
                '',
                f'class {capitalized}Create(BaseModel):',
                '    name: str',
                '    # Add fields here',
                '',
                f'class {capitalized}Update(BaseModel):',
                '    name: str | None = None',
                '    # Add fields here',
            ])

        dep = ", dependencies=[Depends(get_current_user)]" if auth else ""
        lines.extend([
            '',
            f'router = APIRouter(prefix="/{resource}", tags=["{resource.capitalize()}"]{dep})',
            '',
        ])

        if "list" in operations:
            lines.extend([
                f'@router.get("/")',
                f'async def list_{resource}(skip: int = 0, limit: int = 20):',
                f'    """List all {resource}."""',
                '    # ' + resource + ' = await db.' + resource + '.find().skip(skip).limit(limit)',
                '    return {"' + resource + '": [], "total": 0}',
                '', '',
            ])
        if "get" in operations:
            lines.extend([
                '@router.get("/{id}")',
                f'async def get_{singular}(id: str):',
                f'    """Get {singular} by ID."""',
                '    # ' + singular + ' = await db.' + resource + '.find_one({"_id": id})',
                '    # if not ' + singular + ': raise HTTPException(404, "' + capitalized + ' not found")',
                '    return {"id": id}',
                '', '',
            ])
        if "create" in operations:
            body_param = f"data: {capitalized}Create" if validation else "data: dict"
            lines.extend([
                '@router.post("/", status_code=201)',
                f'async def create_{singular}({body_param}):',
                f'    """Create a new {singular}."""',
                '    # result = await db.' + resource + '.insert_one(data)',
                '    return {"message": "' + capitalized + ' created"}',
                '', '',
            ])
        if "update" in operations:
            body_param = f"data: {capitalized}Update" if validation else "data: dict"
            lines.extend([
                '@router.put("/{id}")',
                f'async def update_{singular}(id: str, {body_param}):',
                f'    """Update {singular}."""',
                '    # await db.' + resource + '.update_one({"_id": id}, {"$set": data})',
                '    return {"message": "' + capitalized + ' updated"}',
                '', '',
            ])
        if "delete" in operations:
            lines.extend([
                '@router.delete("/{id}", status_code=204)',
                f'async def delete_{singular}(id: str):',
                f'    """Delete {singular}."""',
                '    # await db.' + resource + '.delete_one({"_id": id})',
                '    return None',
                '',
            ])

        filename = f"routes/{resource}.py"

    # Ensure routes dir
    routes_dir = get_output_dir() / "routes"
    routes_dir.mkdir(exist_ok=True)
    out = get_output_dir() / filename
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"files": [str(out)], "message": f"API Routes generiert ({framework}, /{resource}, {len(operations)} Operationen)"}


# ── Kubernetes Manifests ─────────────────────────────────

@register(
    name="k8s-manifest",
    category="Konfiguration",
    description="Generiert Kubernetes Manifeste (Deployment, Service, Ingress, ConfigMap, HPA)",
    parameters=[
        {"name": "app_name", "type": "text", "description": "App-Name (z.B. my-api)", "required": True},
        {"name": "image", "type": "text", "description": "Container Image (z.B. myapp:latest)", "required": True},
        {"name": "port", "type": "number", "description": "Container Port", "required": False, "default": 3000},
        {"name": "replicas", "type": "number", "description": "Anzahl Replicas", "required": False, "default": 2},
        {"name": "namespace", "type": "text", "description": "Kubernetes Namespace", "required": False},
        {"name": "resources", "type": "multi-select",
         "options": ["deployment", "service", "ingress", "configmap", "hpa", "secret"],
         "description": "Zu generierende Ressourcen", "required": False},
        {"name": "ingress_host", "type": "text", "description": "Ingress Hostname (z.B. api.example.com)", "required": False},
    ],
)
def generate_k8s_manifest(params: dict) -> dict:
    app_name = params.get("app_name", "my-app").strip().lower().replace(" ", "-")
    image = params.get("image", f"{app_name}:latest").strip()
    port = int(params.get("port", 3000))
    replicas = int(params.get("replicas", 2))
    namespace = params.get("namespace", "default").strip() or "default"
    resources = params.get("resources", ["deployment", "service"])
    ingress_host = params.get("ingress_host", f"{app_name}.example.com").strip()
    if isinstance(resources, str):
        resources = [resources] if resources else ["deployment", "service"]

    files = []
    k8s_dir = get_output_dir() / "k8s"
    k8s_dir.mkdir(exist_ok=True)

    labels = f"    app: {app_name}\n    managed-by: assetforge"

    if "deployment" in resources:
        content = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
{labels}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
        - name: {app_name}
          image: {image}
          ports:
            - containerPort: {port}
              protocol: TCP
          env:
            - name: NODE_ENV
              value: "production"
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: {port}
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /health
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 10
      restartPolicy: Always
"""
        out = k8s_dir / "deployment.yaml"
        out.write_text(content, encoding="utf-8")
        files.append(str(out))

    if "service" in resources:
        content = f"""apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
{labels}
spec:
  type: ClusterIP
  selector:
    app: {app_name}
  ports:
    - name: http
      port: 80
      targetPort: {port}
      protocol: TCP
"""
        out = k8s_dir / "service.yaml"
        out.write_text(content, encoding="utf-8")
        files.append(str(out))

    if "ingress" in resources:
        content = f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
{labels}
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - {ingress_host}
      secretName: {app_name}-tls
  rules:
    - host: {ingress_host}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {app_name}
                port:
                  number: 80
"""
        out = k8s_dir / "ingress.yaml"
        out.write_text(content, encoding="utf-8")
        files.append(str(out))

    if "configmap" in resources:
        content = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
  namespace: {namespace}
  labels:
{labels}
data:
  APP_NAME: "{app_name}"
  APP_PORT: "{port}"
  LOG_LEVEL: "info"
  # Add your config values here
"""
        out = k8s_dir / "configmap.yaml"
        out.write_text(content, encoding="utf-8")
        files.append(str(out))

    if "hpa" in resources:
        content = f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
{labels}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: {replicas}
  maxReplicas: {replicas * 5}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
"""
        out = k8s_dir / "hpa.yaml"
        out.write_text(content, encoding="utf-8")
        files.append(str(out))

    if "secret" in resources:
        content = f"""apiVersion: v1
kind: Secret
metadata:
  name: {app_name}-secrets
  namespace: {namespace}
  labels:
{labels}
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@db:5432/{app_name}"
  JWT_SECRET: "change-me-in-production"
  API_KEY: "your-api-key-here"
  # WARNING: Update these values before deploying!
"""
        out = k8s_dir / "secret.yaml"
        out.write_text(content, encoding="utf-8")
        files.append(str(out))

    # Kustomization file if multiple resources
    if len(files) > 1:
        res_files = [f.split("k8s/")[-1].split("k8s\\")[-1] for f in files]
        kustom = "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n\nresources:\n"
        for rf in res_files:
            kustom += f"  - {rf}\n"
        kustom += f"\nnamespace: {namespace}\n"
        kustom += f"\ncommonLabels:\n  app: {app_name}\n"
        out = k8s_dir / "kustomization.yaml"
        out.write_text(kustom, encoding="utf-8")
        files.append(str(out))

    return {"files": files, "message": f"K8s Manifeste generiert ({app_name}, {len(resources)} Ressourcen)"}


# ── Playwright Config ────────────────────────────────────

@register(
    name="playwright-config",
    category="Konfiguration",
    description="Generiert Playwright Test-Konfiguration mit Browser-Setup",
    parameters=[
        {"name": "language", "type": "select", "options": ["typescript", "javascript"],
         "description": "Sprache", "required": False},
        {"name": "browsers", "type": "multi-select",
         "options": ["chromium", "firefox", "webkit", "mobile-chrome", "mobile-safari"],
         "description": "Browser", "required": False},
        {"name": "base_url", "type": "text", "description": "Base URL (z.B. http://localhost:3000)", "required": False},
        {"name": "ci", "type": "boolean", "description": "CI-Modus konfigurieren", "required": False},
        {"name": "screenshot", "type": "select", "options": ["off", "on", "only-on-failure"],
         "description": "Screenshots bei Fehlern", "required": False},
    ],
)
def generate_playwright_config(params: dict) -> dict:
    lang = params.get("language", "typescript")
    browsers = params.get("browsers", ["chromium", "firefox", "webkit"])
    base_url = params.get("base_url", "http://localhost:3000").strip()
    ci = params.get("ci", False)
    screenshot = params.get("screenshot", "only-on-failure")
    if isinstance(browsers, str):
        browsers = [browsers] if browsers else ["chromium"]

    ext = "ts" if lang == "typescript" else "js"
    is_ts = lang == "typescript"

    lines = [
        f'// playwright.config.{ext} — generated by AssetForge',
    ]

    if is_ts:
        lines.extend([
            'import { defineConfig, devices } from "@playwright/test";',
            '',
            'export default defineConfig({',
        ])
    else:
        lines.extend([
            'const { defineConfig, devices } = require("@playwright/test");',
            '',
            'module.exports = defineConfig({',
        ])

    lines.extend([
        f'  testDir: "./tests",',
        f'  fullyParallel: true,',
        f'  forbidOnly: !!process.env.CI,',
        f'  retries: process.env.CI ? 2 : 0,',
        f'  workers: process.env.CI ? 1 : undefined,',
        f'  reporter: process.env.CI ? "github" : "html",',
        '',
        '  use: {',
        f'    baseURL: "{base_url}",',
        '    trace: "on-first-retry",',
        f'    screenshot: "{screenshot}",',
        '    video: "retain-on-failure",',
        '  },',
        '',
        '  projects: [',
    ])

    browser_configs = {
        "chromium": ('    {\n      name: "chromium",\n'
                     '      use: { ...devices["Desktop Chrome"] },\n    },'),
        "firefox": ('    {\n      name: "firefox",\n'
                    '      use: { ...devices["Desktop Firefox"] },\n    },'),
        "webkit": ('    {\n      name: "webkit",\n'
                   '      use: { ...devices["Desktop Safari"] },\n    },'),
        "mobile-chrome": ('    {\n      name: "Mobile Chrome",\n'
                          '      use: { ...devices["Pixel 5"] },\n    },'),
        "mobile-safari": ('    {\n      name: "Mobile Safari",\n'
                          '      use: { ...devices["iPhone 12"] },\n    },'),
    }

    for b in browsers:
        if b in browser_configs:
            lines.append(browser_configs[b])

    lines.append('  ],')

    if ci:
        lines.extend([
            '',
            '  /* Run local dev server before tests */',
            '  // webServer: {',
            f'  //   command: "npm run dev",',
            f'  //   url: "{base_url}",',
            '  //   reuseExistingServer: !process.env.CI,',
            '  // },',
        ])

    lines.extend(['});', ''])

    filename = f"playwright.config.{ext}"
    out = get_output_dir() / filename
    out.write_text("\n".join(lines), encoding="utf-8")
    return {"files": [str(out)], "message": f"Playwright Config generiert ({len(browsers)} Browser, {lang})"}


# ── GitHub Actions Workflow ──────────────────────────────

@register(
    name="github-actions",
    category="Konfiguration",
    description="Generiert GitHub Actions Workflow (CI/CD) mit Matrix-Support",
    parameters=[
        {"name": "workflow_name", "type": "text", "description": "Workflow-Name", "required": False},
        {"name": "trigger", "type": "multi-select",
         "options": ["push", "pull_request", "schedule", "workflow_dispatch"],
         "description": "Trigger-Events", "required": False},
        {"name": "stack", "type": "select",
         "options": ["node", "python", "go", "rust", "docker"],
         "description": "Tech-Stack", "required": True},
        {"name": "node_versions", "type": "text",
         "description": "Node Versionen für Matrix (z.B. 18,20,22)", "required": False},
        {"name": "python_versions", "type": "text",
         "description": "Python Versionen für Matrix (z.B. 3.10,3.11,3.12)", "required": False},
        {"name": "deploy", "type": "boolean", "description": "Deploy-Step inkludieren", "required": False},
        {"name": "cache", "type": "boolean", "description": "Dependency-Caching", "required": False},
    ],
)
def generate_github_actions(params: dict) -> dict:
    import yaml

    name = params.get("workflow_name", "CI").strip() or "CI"
    triggers = params.get("trigger", ["push", "pull_request"])
    stack = params.get("stack", "node")
    deploy = params.get("deploy", False)
    cache = params.get("cache", True)
    if isinstance(triggers, str):
        triggers = [triggers] if triggers else ["push"]

    # Build trigger config
    on_config = {}
    for t in triggers:
        if t == "push":
            on_config["push"] = {"branches": ["main", "master"]}
        elif t == "pull_request":
            on_config["pull_request"] = {"branches": ["main", "master"]}
        elif t == "schedule":
            on_config["schedule"] = [{"cron": "0 6 * * 1"}]  # Monday 6am
        elif t == "workflow_dispatch":
            on_config["workflow_dispatch"] = None

    jobs = {}

    if stack == "node":
        versions_str = params.get("node_versions", "18,20,22").strip()
        versions = [v.strip() for v in versions_str.split(",") if v.strip()]
        if not versions:
            versions = ["20"]

        steps = [
            {"uses": "actions/checkout@v4"},
        ]
        if len(versions) > 1:
            steps.append({
                "name": "Setup Node.js ${{ matrix.node-version }}",
                "uses": "actions/setup-node@v4",
                "with": {"node-version": "${{ matrix.node-version }}"},
            })
        else:
            steps.append({
                "name": f"Setup Node.js {versions[0]}",
                "uses": "actions/setup-node@v4",
                "with": {"node-version": versions[0]},
            })

        if cache:
            steps.append({
                "name": "Cache node_modules",
                "uses": "actions/cache@v4",
                "with": {
                    "path": "node_modules",
                    "key": "${{ runner.os }}-node-${{ hashFiles('package-lock.json') }}",
                    "restore-keys": "${{ runner.os }}-node-",
                },
            })

        steps.extend([
            {"name": "Install dependencies", "run": "npm ci"},
            {"name": "Lint", "run": "npm run lint --if-present"},
            {"name": "Test", "run": "npm test --if-present"},
            {"name": "Build", "run": "npm run build --if-present"},
        ])

        build_job = {
            "runs-on": "ubuntu-latest",
            "steps": steps,
        }
        if len(versions) > 1:
            build_job["strategy"] = {"matrix": {"node-version": versions}}

        jobs["build"] = build_job

    elif stack == "python":
        versions_str = params.get("python_versions", "3.11,3.12").strip()
        versions = [v.strip() for v in versions_str.split(",") if v.strip()]
        if not versions:
            versions = ["3.12"]

        steps = [
            {"uses": "actions/checkout@v4"},
        ]
        ver_ref = "${{ matrix.python-version }}" if len(versions) > 1 else versions[0]
        steps.append({
            "name": f"Setup Python {ver_ref}",
            "uses": "actions/setup-python@v5",
            "with": {"python-version": ver_ref},
        })

        if cache:
            steps.append({
                "name": "Cache pip",
                "uses": "actions/cache@v4",
                "with": {
                    "path": "~/.cache/pip",
                    "key": "${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}",
                },
            })

        steps.extend([
            {"name": "Install dependencies", "run": "pip install -r requirements.txt"},
            {"name": "Lint", "run": "pip install ruff && ruff check ."},
            {"name": "Test", "run": "python -m pytest --tb=short -q"},
        ])

        build_job = {"runs-on": "ubuntu-latest", "steps": steps}
        if len(versions) > 1:
            build_job["strategy"] = {"matrix": {"python-version": versions}}
        jobs["build"] = build_job

    elif stack == "go":
        steps = [
            {"uses": "actions/checkout@v4"},
            {"name": "Setup Go", "uses": "actions/setup-go@v5", "with": {"go-version": "stable"}},
            {"name": "Build", "run": "go build ./..."},
            {"name": "Test", "run": "go test -v -race ./..."},
            {"name": "Vet", "run": "go vet ./..."},
        ]
        jobs["build"] = {"runs-on": "ubuntu-latest", "steps": steps}

    elif stack == "rust":
        steps = [
            {"uses": "actions/checkout@v4"},
            {"name": "Setup Rust", "uses": "dtolnay/rust-toolchain@stable"},
        ]
        if cache:
            steps.append({"name": "Cache cargo", "uses": "Swatinem/rust-cache@v2"})
        steps.extend([
            {"name": "Check", "run": "cargo check"},
            {"name": "Test", "run": "cargo test"},
            {"name": "Clippy", "run": "cargo clippy -- -D warnings"},
            {"name": "Format", "run": "cargo fmt --check"},
        ])
        jobs["build"] = {"runs-on": "ubuntu-latest", "steps": steps}

    elif stack == "docker":
        steps = [
            {"uses": "actions/checkout@v4"},
            {"name": "Set up Docker Buildx", "uses": "docker/setup-buildx-action@v3"},
            {"name": "Build image", "run": "docker build -t app:test ."},
            {"name": "Run tests", "run": "docker run --rm app:test npm test || true"},
        ]
        jobs["build"] = {"runs-on": "ubuntu-latest", "steps": steps}

    if deploy:
        deploy_steps = [
            {"uses": "actions/checkout@v4"},
            {"name": "Deploy", "run": 'echo "Add your deploy commands here"'},
        ]
        jobs["deploy"] = {
            "runs-on": "ubuntu-latest",
            "needs": "build",
            "if": "github.ref == 'refs/heads/main' && github.event_name == 'push'",
            "steps": deploy_steps,
        }

    workflow = {"name": name, "on": on_config, "jobs": jobs}

    # Write YAML
    gh_dir = get_output_dir() / ".github" / "workflows"
    gh_dir.mkdir(parents=True, exist_ok=True)
    filename = name.lower().replace(" ", "-") + ".yml"
    out = gh_dir / filename

    yaml_content = yaml.dump(workflow, default_flow_style=False, sort_keys=False, allow_unicode=True)
    out.write_text(yaml_content, encoding="utf-8")

    features = [stack]
    if deploy:
        features.append("Deploy")
    if cache:
        features.append("Cache")
    return {"files": [str(out)], "message": f"GitHub Actions Workflow generiert ({', '.join(features)})"}

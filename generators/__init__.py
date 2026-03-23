"""Asset Generator Registry - zentrale Verwaltung aller Generatoren."""

import shutil
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Configurable target directory (set via API)
_target_dir: Path | None = None

# Registry: name -> {handler, category, description, parameters}
_registry: dict[str, dict] = {}

# Preset definitions
PRESETS: dict[str, dict] = {
    "python-project": {
        "label": "Python-Projekt",
        "description": "Komplettes Setup für ein Python-Projekt (README, License, Gitignore, Dockerfile, .env, CI/CD, Changelog)",
        "generators": [
            {"name": "readme", "params": {"stack": "python", "badges": True, "has_env": True}},
            {"name": "license", "params": {"license_type": "mit"}},
            {"name": "gitignore", "params": {"stacks": ["python", "general"]}},
            {"name": "dockerfile", "params": {"stack": "python", "port": 8000}},
            {"name": "env", "params": {"include_db": True}},
            {"name": "ci", "params": {"platform": "github", "stack": "python", "run_tests": True, "run_lint": True}},
            {"name": "changelog", "params": {}},
            {"name": "contributing", "params": {"stack": "python"}},
        ],
    },
    "node-project": {
        "label": "Node.js-Projekt",
        "description": "Komplettes Setup für ein Node.js-Projekt (README, License, Gitignore, Dockerfile, .env, CI/CD, Changelog)",
        "generators": [
            {"name": "readme", "params": {"stack": "node", "badges": True, "has_env": True}},
            {"name": "license", "params": {"license_type": "mit"}},
            {"name": "gitignore", "params": {"stacks": ["node", "general"]}},
            {"name": "dockerfile", "params": {"stack": "node", "port": 3000}},
            {"name": "env", "params": {"include_db": True}},
            {"name": "ci", "params": {"platform": "github", "stack": "node", "run_tests": True, "run_lint": True}},
            {"name": "changelog", "params": {}},
            {"name": "contributing", "params": {"stack": "node"}},
        ],
    },
    "fullstack-project": {
        "label": "Fullstack-Projekt",
        "description": "Alles: Docs, Configs, Docker-Compose mit DB & Redis, CI/CD, Farbpalette, Logo",
        "generators": [
            {"name": "readme", "params": {"stack": "node", "badges": True, "has_api": True, "has_env": True}},
            {"name": "license", "params": {"license_type": "mit"}},
            {"name": "gitignore", "params": {"stacks": ["node", "python", "general"]}},
            {"name": "compose", "params": {"services": ["app", "postgres", "redis", "nginx"]}},
            {"name": "env", "params": {"include_db": True, "include_auth": True}},
            {"name": "ci", "params": {"platform": "github", "stack": "node", "run_tests": True, "run_lint": True, "deploy": True}},
            {"name": "changelog", "params": {}},
            {"name": "contributing", "params": {"stack": "node"}},
            {"name": "palette", "params": {"base_color": "#e94560", "harmony": "analogous", "count": 5}},
            {"name": "robots-txt", "params": {"policy": "custom", "blocked_paths": "/admin,/api"}},
        ],
    },
    "api-backend": {
        "label": "API-Backend",
        "description": "Backend-API Setup mit DB-Schema, Docker, Docs, CI/CD und Security",
        "generators": [
            {"name": "readme", "params": {"stack": "python", "badges": True, "has_api": True, "has_env": True}},
            {"name": "license", "params": {"license_type": "mit"}},
            {"name": "gitignore", "params": {"stacks": ["python", "general"]}},
            {"name": "dockerfile", "params": {"stack": "python", "port": 8000}},
            {"name": "dockerignore", "params": {"stacks": ["python", "general"]}},
            {"name": "compose", "params": {"services": ["app", "postgres", "redis"]}},
            {"name": "env", "params": {"include_db": True, "include_auth": True}},
            {"name": "ci", "params": {"platform": "github", "stack": "python", "run_tests": True, "run_lint": True}},
            {"name": "changelog", "params": {}},
            {"name": "robots-txt", "params": {"policy": "custom", "blocked_paths": "/admin,/api,/docs"}},
        ],
    },
    "react-app": {
        "label": "React-App",
        "description": "Komplettes React-Setup mit Vite, ESLint, Prettier, Tests und Komponenten-Boilerplate",
        "generators": [
            {"name": "readme", "params": {"stack": "node", "badges": True}},
            {"name": "license", "params": {"license_type": "mit"}},
            {"name": "gitignore", "params": {"stacks": ["node", "general"]}},
            {"name": "vite-config", "params": {"framework": "react", "port": 5173}},
            {"name": "eslintrc", "params": {"framework": "react", "typescript": True, "prettier": True}},
            {"name": "prettierrc", "params": {"semi": True, "single_quote": True, "tab_width": 2}},
            {"name": "tsconfig", "params": {"framework": "react"}},
            {"name": "vitest-config", "params": {"framework": "react", "coverage": True}},
            {"name": "react-component", "params": {"name": "App", "typescript": True, "styling": "css-modules"}},
            {"name": "favicon", "params": {"text": "R", "bg_color": "#61dafb"}},
        ],
    },
    "static-website": {
        "label": "Statische Website",
        "description": "Setup für eine statische Website mit Vite, Tailwind, Security und Docs",
        "generators": [
            {"name": "readme", "params": {"stack": "node", "badges": True}},
            {"name": "license", "params": {"license_type": "mit"}},
            {"name": "gitignore", "params": {"stacks": ["node", "general"]}},
            {"name": "vite-config", "params": {"framework": "vanilla", "port": 5173}},
            {"name": "tailwind-config", "params": {"dark_mode": "class"}},
            {"name": "prettierrc", "params": {"semi": True, "single_quote": True, "tab_width": 2}},
            {"name": "robots-txt", "params": {"policy": "allow-all"}},
            {"name": "favicon", "params": {"text": "S", "bg_color": "#3b82f6"}},
        ],
    },
}


def set_target_dir(path: str | None):
    """Set a custom output directory. None resets to default."""
    global _target_dir
    if path:
        _target_dir = Path(path)
        _target_dir.mkdir(parents=True, exist_ok=True)
    else:
        _target_dir = None


def get_output_dir() -> Path:
    return _target_dir if _target_dir else OUTPUT_DIR


def register(name: str, category: str, description: str, parameters: list[dict]):
    """Decorator to register a generator function."""
    def decorator(func):
        _registry[name] = {
            "handler": func,
            "category": category,
            "description": description,
            "parameters": parameters,
        }
        return func
    return decorator


def get_generator(name: str) -> dict | None:
    return _registry.get(name)


def list_generators() -> dict[str, list[dict]]:
    """Return generators grouped by category."""
    grouped: dict[str, list[dict]] = {}
    for name, gen in _registry.items():
        cat = gen["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "name": name,
            "description": gen["description"],
            "parameters": gen["parameters"],
        })
    return grouped


def list_presets() -> dict[str, dict]:
    """Return available presets with label and description."""
    return {k: {"label": v["label"], "description": v["description"]} for k, v in PRESETS.items()}


def generate(name: str, params: dict) -> dict:
    """Run a generator by name with given params. Returns {files: [...], message: str}."""
    gen = _registry.get(name)
    if not gen:
        raise ValueError(f"Unknown generator: {name}")
    out = get_output_dir()
    out.mkdir(exist_ok=True)
    return gen["handler"](params)


def run_preset(preset_name: str, overrides: dict | None = None) -> dict:
    """Run all generators in a preset. Overrides are merged into each generator's params."""
    preset = PRESETS.get(preset_name)
    if not preset:
        raise ValueError(f"Unknown preset: {preset_name}")

    overrides = overrides or {}
    results = []
    all_files = []

    for gen_def in preset["generators"]:
        name = gen_def["name"]
        params = {**gen_def["params"], **overrides}
        try:
            result = generate(name, params)
            results.append({"name": name, "status": "ok", **result})
            all_files.extend(result.get("files", []))
        except Exception as e:
            results.append({"name": name, "status": "error", "message": str(e)})

    return {"preset": preset_name, "label": preset["label"], "results": results, "total_files": len(all_files)}

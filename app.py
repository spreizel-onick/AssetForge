"""Asset-Generator Tool — FastAPI Backend."""

import json
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Import all generator modules so they register themselves
from generators import (
    list_generators, generate, get_output_dir, set_target_dir,
    list_presets, run_preset, OUTPUT_DIR,
)
import generators.config    # noqa: F401
import generators.docs      # noqa: F401
import generators.database   # noqa: F401
import generators.visual     # noqa: F401
import generators.security   # noqa: F401
import generators.code       # noqa: F401

app = FastAPI(title="AssetForge", version="3.3.0")

# ── History & Favorites Storage ────────────────────────────
DATA_DIR = Path(__file__).parent / ".assetforge"
HISTORY_FILE = DATA_DIR / "history.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"


def _load_json(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def _save_json(path: Path, data: list):
    DATA_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


# ── Generators ──────────────────────────────────────────────

@app.get("/api/generators")
async def api_generators():
    return list_generators()


@app.post("/api/generate/{name}")
async def api_generate(name: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        result = generate(name, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save to history
    history = _load_json(HISTORY_FILE)
    history.insert(0, {
        "id": len(history) + 1,
        "generator": name,
        "params": body,
        "files": result.get("files", []),
        "timestamp": datetime.now().isoformat(),
        "type": "generator",
    })
    if len(history) > 100:
        history = history[:100]
    _save_json(HISTORY_FILE, history)
    return result


@app.post("/api/generate-bundle")
async def api_generate_bundle(request: Request):
    """Generate multiple assets at once."""
    body = await request.json()
    generators_list = body.get("generators", [])
    results = []
    all_files = []
    for gen in generators_list:
        name = gen.get("name")
        params = gen.get("params", {})
        try:
            result = generate(name, params)
            results.append({"name": name, "status": "ok", **result})
            all_files.extend(result.get("files", []))
        except Exception as e:
            results.append({"name": name, "status": "error", "message": str(e)})
    return {"results": results, "total_files": len(all_files)}


# ── Presets ─────────────────────────────────────────────────

@app.get("/api/presets")
async def api_presets():
    return list_presets()


@app.post("/api/presets/{preset_name}")
async def api_run_preset(preset_name: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        result = run_preset(preset_name, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save to history
    all_files = []
    for r in result.get("results", []):
        all_files.extend(r.get("files", []))
    history = _load_json(HISTORY_FILE)
    history.insert(0, {
        "id": len(history) + 1,
        "generator": preset_name,
        "params": body,
        "files": all_files,
        "timestamp": datetime.now().isoformat(),
        "type": "preset",
    })
    if len(history) > 100:
        history = history[:100]
    _save_json(HISTORY_FILE, history)
    return result


# ── History ────────────────────────────────────────────────

@app.get("/api/history")
async def api_history():
    return _load_json(HISTORY_FILE)


@app.delete("/api/history/{index}")
async def api_delete_history(index: int):
    """Delete a history entry and optionally its files."""
    history = _load_json(HISTORY_FILE)
    if index < 0 or index >= len(history):
        raise HTTPException(status_code=404, detail="History entry not found")
    entry = history.pop(index)
    _save_json(HISTORY_FILE, history)
    return {"deleted": entry}


@app.delete("/api/history")
async def api_clear_history():
    """Clear all history entries."""
    _save_json(HISTORY_FILE, [])
    return {"message": "History gelöscht"}


@app.post("/api/history/{index}/undo")
async def api_undo_history(index: int):
    """Undo a history entry by deleting its generated files."""
    history = _load_json(HISTORY_FILE)
    if index < 0 or index >= len(history):
        raise HTTPException(status_code=404, detail="History entry not found")
    entry = history[index]
    deleted_files = []
    for f in entry.get("files", []):
        fp = Path(f)
        if fp.exists():
            fp.unlink()
            deleted_files.append(str(fp))
    history.pop(index)
    _save_json(HISTORY_FILE, history)
    return {"deleted_files": deleted_files, "count": len(deleted_files)}


# ── Favorites ──────────────────────────────────────────────

@app.get("/api/favorites")
async def api_favorites():
    return _load_json(FAVORITES_FILE)


@app.post("/api/favorites")
async def api_add_favorite(request: Request):
    body = await request.json()
    favs = _load_json(FAVORITES_FILE)
    favs.append({
        "name": body.get("name", "Unbenannt"),
        "generator": body.get("generator"),
        "type": body.get("type", "generator"),
        "params": body.get("params", {}),
        "created": datetime.now().isoformat(),
    })
    _save_json(FAVORITES_FILE, favs)
    return {"count": len(favs)}


@app.delete("/api/favorites/{index}")
async def api_delete_favorite(index: int):
    favs = _load_json(FAVORITES_FILE)
    if index < 0 or index >= len(favs):
        raise HTTPException(status_code=404, detail="Favorite not found")
    removed = favs.pop(index)
    _save_json(FAVORITES_FILE, favs)
    return {"removed": removed}


@app.get("/api/favorites/export")
async def api_export_favorites():
    """Export favorites as JSON download."""
    favs = _load_json(FAVORITES_FILE)
    content = json.dumps(favs, indent=2, ensure_ascii=False).encode("utf-8")
    return StreamingResponse(
        BytesIO(content),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=assetforge-favorites.json"},
    )


@app.post("/api/favorites/import")
async def api_import_favorites(request: Request):
    """Import favorites from JSON. Merges with existing, skips duplicates."""
    body = await request.json()
    imported = body.get("favorites", [])
    if not isinstance(imported, list):
        raise HTTPException(400, "Invalid format: expected {favorites: [...]}")
    existing = _load_json(FAVORITES_FILE)
    # Deduplicate by generator+name combo
    existing_keys = {(f.get("generator"), f.get("name")) for f in existing}
    added = 0
    for fav in imported:
        key = (fav.get("generator"), fav.get("name"))
        if key not in existing_keys:
            existing.append(fav)
            existing_keys.add(key)
            added += 1
    _save_json(FAVORITES_FILE, existing)
    return {"added": added, "total": len(existing), "skipped": len(imported) - added}


# ── File Check (overwrite warning) ─────────────────────────

@app.post("/api/check-files")
async def api_check_files(request: Request):
    """Check if files would be overwritten."""
    body = await request.json()
    files = body.get("files", [])
    out = get_output_dir()
    existing = []
    for f in files:
        fp = out / f
        if fp.exists():
            existing.append({"name": f, "size": fp.stat().st_size})
    return {"existing": existing, "count": len(existing)}


# ── Statistics ─────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats():
    """Return usage statistics for the welcome page."""
    out = get_output_dir()
    out.mkdir(exist_ok=True)
    files = list(out.rglob("*"))
    file_count = sum(1 for f in files if f.is_file())
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    history = _load_json(HISTORY_FILE)
    return {
        "file_count": file_count,
        "total_size": total_size,
        "history_count": len(history),
        "last_generation": history[0]["timestamp"] if history else None,
    }


# ── Delete Output Files ───────────────────────────────────

@app.delete("/api/output/{filepath:path}")
async def api_delete_output_file(filepath: str):
    full = get_output_dir() / filepath
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    full.unlink()
    return {"deleted": filepath}


@app.delete("/api/output")
async def api_clear_output():
    """Delete all generated files."""
    out = get_output_dir()
    count = 0
    for f in list(out.rglob("*")):
        if f.is_file():
            f.unlink()
            count += 1
    # Remove empty dirs
    for d in sorted(out.rglob("*"), reverse=True):
        if d.is_dir() and not list(d.iterdir()):
            d.rmdir()
    return {"deleted": count}


# ── Output Settings ─────────────────────────────────────────

@app.get("/api/settings")
async def api_get_settings():
    return {"output_dir": str(get_output_dir())}


@app.post("/api/settings")
async def api_set_settings(request: Request):
    body = await request.json()
    output_dir = body.get("output_dir")
    if output_dir:
        target = Path(output_dir)
        if not target.parent.exists():
            raise HTTPException(status_code=400, detail=f"Parent directory does not exist: {target.parent}")
        set_target_dir(output_dir)
    else:
        set_target_dir(None)
    return {"output_dir": str(get_output_dir()), "message": "Output-Verzeichnis aktualisiert"}


# ── Output Files ────────────────────────────────────────────

@app.get("/api/output")
async def api_list_output():
    out = get_output_dir()
    out.mkdir(exist_ok=True)
    files = []
    for f in sorted(out.rglob("*")):
        if f.is_file():
            rel = f.relative_to(out)
            files.append({
                "name": str(rel),
                "size": f.stat().st_size,
                "path": str(f),
            })
    return {"files": files, "output_dir": str(out)}


@app.get("/api/output/{filepath:path}")
async def api_download_file(filepath: str):
    full = get_output_dir() / filepath
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(full), filename=full.name)


@app.get("/api/preview/{filepath:path}")
async def api_preview_file(filepath: str):
    """Return file content for in-app preview."""
    full = get_output_dir() / filepath
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    suffix = full.suffix.lower()
    is_image = suffix in (".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg")
    is_text = suffix in (
        ".md", ".txt", ".yml", ".yaml", ".json", ".css", ".js", ".ts",
        ".py", ".sql", ".html", ".env", ".toml", ".cfg", ".ini", "",
    ) or full.name.startswith(".") or full.name == "Makefile"

    if is_image:
        import base64
        data = base64.b64encode(full.read_bytes()).decode()
        mime = "image/png" if suffix == ".png" else f"image/{suffix.lstrip('.')}"
        return {"type": "image", "mime": mime, "data": data, "name": full.name}
    elif is_text:
        try:
            content = full.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = full.read_text(encoding="latin-1")
        lang = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".sql": "sql", ".yml": "yaml", ".yaml": "yaml", ".json": "json",
            ".md": "markdown", ".html": "html", ".css": "css", ".toml": "toml",
        }.get(suffix, "text")
        return {"type": "text", "lang": lang, "content": content, "name": full.name}
    else:
        return {"type": "binary", "name": full.name, "size": full.stat().st_size}


@app.get("/api/download-zip")
async def api_download_zip():
    """Download all generated files as a ZIP archive."""
    out = get_output_dir()
    out.mkdir(exist_ok=True)
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in out.rglob("*"):
            if f.is_file():
                zf.write(str(f), str(f.relative_to(out)))
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=assetforge-output.zip"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)

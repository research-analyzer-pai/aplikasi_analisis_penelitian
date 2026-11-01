"""Project workspace and extension registry for Research Analyzer Web v6.0."""
from __future__ import annotations
import io, json, zipfile, re
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

PROJECT_VERSION = "1.0"

def safe_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "project")).strip("_")
    return value[:70] or "project"

def create_project_bundle(metadata: dict, frames: dict[str, pd.DataFrame | None],
                          notes: dict | None = None) -> bytes:
    """Create portable ZIP project with metadata and CSV datasets."""
    manifest = {
        "format": "research-analyzer-project",
        "format_version": PROJECT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
        "notes": notes or {},
        "datasets": {}
    }
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, frame in (frames or {}).items():
            if frame is not None and isinstance(frame, pd.DataFrame) and not frame.empty:
                safe = safe_slug(name) + ".csv"
                zf.writestr("datasets/" + safe, frame.to_csv(index=False))
                manifest["datasets"][name] = "datasets/" + safe
        zf.writestr("project.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("README.txt",
            "Research Analyzer Professional Web project bundle.\n"
            "Data CSV disimpan dalam folder datasets. Periksa anonimisasi sebelum berbagi.\n")
    return out.getvalue()

def read_project_bundle(file_bytes: bytes) -> tuple[dict, dict[str, pd.DataFrame]]:
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        bad = zf.testzip()
        if bad: raise ValueError(f"Arsip rusak pada: {bad}")
        if "project.json" not in zf.namelist():
            raise ValueError("project.json tidak ditemukan; file bukan paket proyek yang valid.")
        manifest = json.loads(zf.read("project.json").decode("utf-8"))
        if manifest.get("format") != "research-analyzer-project":
            raise ValueError("Format proyek tidak dikenali.")
        frames = {}
        for name, member in manifest.get("datasets", {}).items():
            if member not in zf.namelist() or not member.startswith("datasets/"):
                raise ValueError(f"Dataset tidak valid: {name}")
            frames[name] = pd.read_csv(io.BytesIO(zf.read(member)))
        return manifest, frames

def discover_extensions(directory: str | Path = "extensions") -> list[dict]:
    """Discover Python extension modules without importing or executing them."""
    base = Path(directory)
    base.mkdir(parents=True, exist_ok=True)
    found = []
    for path in sorted(base.glob("*.py")):
        if path.name.startswith("_"): continue
        found.append({"name": path.stem, "file": str(path), "bytes": path.stat().st_size})
    return found

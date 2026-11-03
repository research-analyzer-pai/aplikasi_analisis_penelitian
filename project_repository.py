"""Persistent project repository for Research Analyzer Professional.

Local development: SQLite.
Streamlit Cloud: PostgreSQL is required for durable persistence. Configure
DATABASE_URL in Streamlit Community Cloud > App settings > Secrets.
"""
from __future__ import annotations

import json
import os
from io import StringIO
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _read_database_url() -> str:
    """Read DATABASE_URL from environment first, then Streamlit secrets."""
    value = os.environ.get("DATABASE_URL", "").strip()
    if value:
        return value
    try:
        import streamlit as st
        value = str(st.secrets.get("DATABASE_URL", "")).strip()
    except Exception:
        value = ""
    return value


def _normalise_database_url(url: str) -> str:
    """Normalise common hosted-Postgres URL formats for psycopg v3."""
    url = (url or "").strip().strip('"').strip("'")
    if not url:
        return ""

    # Providers may supply postgres:// or postgresql:// URLs.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    # Use psycopg v3 explicitly, which is installed by requirements.txt.
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    return url


def get_database_config() -> dict:
    """Return safe configuration diagnostics without exposing credentials."""
    raw_url = _read_database_url()
    url = _normalise_database_url(raw_url)
    if not url:
        return {
            "configured": False,
            "backend": "sqlite",
            "url": "",
            "message": "DATABASE_URL belum diatur; SQLite digunakan.",
        }

    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"postgresql+psycopg", "postgresql"}:
            return {
                "configured": True,
                "backend": "invalid",
                "url": "",
                "message": "DATABASE_URL harus menggunakan PostgreSQL.",
            }
        if not parsed.hostname or not parsed.path.strip("/"):
            return {
                "configured": True,
                "backend": "invalid",
                "url": "",
                "message": "Format DATABASE_URL belum lengkap (host atau nama database tidak ditemukan).",
            }
    except Exception:
        return {
            "configured": True,
            "backend": "invalid",
            "url": "",
            "message": "Format DATABASE_URL tidak valid.",
        }

    return {
        "configured": True,
        "backend": "postgresql",
        "url": url,
        "message": "Konfigurasi PostgreSQL ditemukan.",
    }


def get_engine() -> Engine:
    config = get_database_config()
    if config["backend"] == "invalid":
        raise ValueError(config["message"])

    if config["backend"] == "postgresql":
        # pool_pre_ping detects dropped connections on hosted database services.
        return create_engine(
            config["url"],
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": 15},
        )

    # SQLite is intentionally the local-development fallback only.
    return create_engine(
        "sqlite:///research_analyzer_v60.db",
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )


def check_database_connection(engine: Engine) -> tuple[bool, str]:
    """Run a minimal health check and return a user-safe diagnostic."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Koneksi database berhasil."
    except Exception as exc:
        # Avoid exposing a full URL/password in the UI.
        message = str(exc).splitlines()[0][:240]
        return False, f"Koneksi database gagal: {message}"


def init_repository(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS research_projects (
                project_id VARCHAR(255) PRIMARY KEY,
                project_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))


def _frame_to_obj(frame: Any) -> dict | None:
    if not isinstance(frame, pd.DataFrame):
        return None
    return json.loads(frame.to_json(
        orient="table", date_format="iso", force_ascii=False
    ))


def _obj_to_frame(obj: dict | None, default_columns=None) -> pd.DataFrame:
    if not obj:
        return pd.DataFrame(columns=default_columns or [])
    try:
        return pd.read_json(
            StringIO(json.dumps(obj, ensure_ascii=False)), orient="table"
        )
    except Exception:
        return pd.DataFrame(
            obj.get("data", []), columns=obj.get("columns", default_columns)
        )


def serialize_state(state: dict) -> str:
    payload = {
        "data": _frame_to_obj(state.get("data")),
        "tabular_datasets": {
            str(k): _frame_to_obj(v)
            for k, v in (state.get("tabular_datasets") or {}).items()
        },
        "segments": _frame_to_obj(state.get("segments")),
        "codes": _frame_to_obj(state.get("codes")),
        "sem": _frame_to_obj(state.get("sem")),
        "data_sources": state.get("data_sources", []),
        "ingested_hashes": sorted(list(state.get("ingested_hashes", set()))),
        "joint": state.get("joint", []),
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def deserialize_state(payload_text: str) -> dict:
    payload = json.loads(payload_text)
    return {
        "data": _obj_to_frame(payload.get("data")),
        "tabular_datasets": {
            k: _obj_to_frame(v)
            for k, v in payload.get("tabular_datasets", {}).items()
        },
        "segments": _obj_to_frame(
            payload.get("segments"),
            ["id", "source", "participant", "text"],
        ),
        "codes": _obj_to_frame(
            payload.get("codes"),
            ["segment_id", "code", "category", "theme", "memo", "evidence_type"],
        ),
        "sem": _obj_to_frame(payload.get("sem")),
        "data_sources": payload.get("data_sources", []),
        "ingested_hashes": set(payload.get("ingested_hashes", [])),
        "joint": payload.get("joint", []),
    }


def save_project(engine: Engine, project_id: str, project_name: str, state: dict) -> None:
    payload = serialize_state(state)
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT project_id FROM research_projects WHERE project_id=:pid"),
            {"pid": project_id},
        ).first()
        if exists:
            conn.execute(text("""
                UPDATE research_projects
                SET project_name=:name, payload=:payload, updated_at=:updated
                WHERE project_id=:pid
            """), {
                "pid": project_id, "name": project_name,
                "payload": payload, "updated": now,
            })
        else:
            conn.execute(text("""
                INSERT INTO research_projects(project_id, project_name, payload, updated_at)
                VALUES(:pid, :name, :payload, :updated)
            """), {
                "pid": project_id, "name": project_name,
                "payload": payload, "updated": now,
            })


def load_project(engine: Engine, project_id: str) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT payload FROM research_projects WHERE project_id=:pid"),
            {"pid": project_id},
        ).first()
    return deserialize_state(row[0]) if row else None


def list_projects(engine: Engine) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT project_id, project_name, updated_at
            FROM research_projects ORDER BY updated_at DESC
        """)).mappings().all()
    return [dict(r) for r in rows]


def database_mode(engine: Engine) -> str:
    return (
        "PostgreSQL — penyimpanan cloud persisten"
        if engine.dialect.name == "postgresql"
        else "SQLite — mode lokal, tidak dijamin permanen di cloud"
    )

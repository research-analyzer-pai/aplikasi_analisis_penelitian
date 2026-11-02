"""Persistent project repository for Research Analyzer Professional v6.0.

Uses PostgreSQL when DATABASE_URL is configured (recommended for Streamlit Cloud),
otherwise SQLite for local development. Stores parsed project datasets and research
materials as JSON payloads; original uploads are not retained as binary files.
"""
from __future__ import annotations
import json
import os
from io import StringIO
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        try:
            import streamlit as st
            url = str(st.secrets.get("DATABASE_URL", "")).strip()
        except Exception:
            url = ""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url or "sqlite:///research_analyzer_v60.db"


def get_engine() -> Engine:
    url = _database_url()
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


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
    # JSON table format retains column labels and most common dtypes safely.
    return json.loads(frame.to_json(orient="table", date_format="iso", force_ascii=False))


def _obj_to_frame(obj: dict | None, default_columns=None) -> pd.DataFrame:
    if not obj:
        return pd.DataFrame(columns=default_columns or [])
    try:
        return pd.read_json(StringIO(json.dumps(obj, ensure_ascii=False)), orient="table")
    except Exception:
        return pd.DataFrame(obj.get("data", []), columns=obj.get("columns", default_columns))


def serialize_state(state: dict) -> str:
    payload = {
        "data": _frame_to_obj(state.get("data")),
        "tabular_datasets": {str(k): _frame_to_obj(v) for k, v in (state.get("tabular_datasets") or {}).items()},
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
        "tabular_datasets": {k: _obj_to_frame(v) for k, v in payload.get("tabular_datasets", {}).items()},
        "segments": _obj_to_frame(payload.get("segments"), ["id", "source", "participant", "text"]),
        "codes": _obj_to_frame(payload.get("codes"), ["segment_id", "code", "category", "theme", "memo", "evidence_type"]),
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
            {"pid": project_id}
        ).first()
        if exists:
            conn.execute(text("""
                UPDATE research_projects
                SET project_name=:name, payload=:payload, updated_at=:updated
                WHERE project_id=:pid
            """), {"pid": project_id, "name": project_name, "payload": payload, "updated": now})
        else:
            conn.execute(text("""
                INSERT INTO research_projects(project_id, project_name, payload, updated_at)
                VALUES(:pid, :name, :payload, :updated)
            """), {"pid": project_id, "name": project_name, "payload": payload, "updated": now})


def load_project(engine: Engine, project_id: str) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT payload FROM research_projects WHERE project_id=:pid"),
            {"pid": project_id}
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
    return "PostgreSQL (persistent cloud database)" if engine.dialect.name == "postgresql" else "SQLite (local/session host storage)"

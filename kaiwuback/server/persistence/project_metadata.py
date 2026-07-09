"""Project library metadata persistence with sidecar fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.config import IMG_STORE, PROJECT_LIB
from server.persistence.db import transaction

PROJECT_FOLDER_META = PROJECT_LIB / ".folder-meta.json"
PROJECT_FILE_META = PROJECT_LIB / ".file-meta.json"
PROJECT_FOLDER_STATE = PROJECT_LIB / ".folder-state.json"
PROJECT_IMAGE_META = IMG_STORE / ".image-meta.json"

_db_available = True
_db_warning_printed = False
_backfill_attempted = False


def _mark_db_unavailable(exc: Exception) -> None:
    global _db_available, _db_warning_printed
    _db_available = False
    if not _db_warning_printed:
        print(f"[PROJECT_META] MySQL unavailable, using sidecar metadata: {str(exc)[:120]}", flush=True)
        _db_warning_printed = True


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception as exc:
        print(f"[PROJECT_META] Sidecar read failed for {path.name}: {str(exc)[:120]}", flush=True)
        return fallback


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _read_folder_meta_sidecar() -> dict[str, str]:
    data = _read_json(PROJECT_FOLDER_META, {})
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value or "") for key, value in data.items()}


def _write_folder_meta_sidecar(meta: dict[str, str]) -> None:
    _write_json(PROJECT_FOLDER_META, meta)


def _read_file_meta_sidecar() -> dict[str, dict[str, Any]]:
    data = _read_json(PROJECT_FILE_META, {})
    if not isinstance(data, dict):
        return {}
    return {str(key): value for key, value in data.items() if isinstance(value, dict)}


def _write_file_meta_sidecar(meta: dict[str, dict[str, Any]]) -> None:
    _write_json(PROJECT_FILE_META, meta)


def _read_folder_state_sidecar() -> dict[str, object]:
    data = _read_json(PROJECT_FOLDER_STATE, {"hidden": [], "display_names": {}})
    if not isinstance(data, dict):
        return {"hidden": [], "display_names": {}}
    hidden = data.get("hidden", [])
    display_names = data.get("display_names", {})
    if not isinstance(hidden, list):
        hidden = []
    if not isinstance(display_names, dict):
        display_names = {}
    return {
        "hidden": [str(name) for name in hidden],
        "display_names": {str(key): str(value or "") for key, value in display_names.items()},
    }


def _write_folder_state_sidecar(state: dict[str, object]) -> None:
    _write_json(PROJECT_FOLDER_STATE, state)


def _read_image_meta_sidecar() -> dict[str, dict[str, Any]]:
    data = _read_json(PROJECT_IMAGE_META, {})
    if not isinstance(data, dict):
        return {}
    return {str(key): value for key, value in data.items() if isinstance(value, dict)}


def _write_image_meta_sidecar(meta: dict[str, dict[str, Any]]) -> None:
    _write_json(PROJECT_IMAGE_META, meta)


def _iter_file_meta_rows(meta: dict[str, dict[str, Any]]):
    for key, value in meta.items():
        if "/" not in key or not isinstance(value, dict):
            continue
        folder_name, filename = key.split("/", 1)
        if folder_name and filename:
            yield folder_name, filename, value


def _iter_image_meta_rows(meta: dict[str, dict[str, Any]]):
    for filename, value in meta.items():
        if filename and isinstance(value, dict):
            yield filename, value


def _backfill_sidecars_to_db_once() -> None:
    """Seed empty metadata tables from legacy JSON sidecars once per process."""
    global _backfill_attempted
    if not _db_available or _backfill_attempted:
        return

    _backfill_attempted = True
    folder_meta = _read_folder_meta_sidecar()
    folder_state = _read_folder_state_sidecar()
    file_meta = _read_file_meta_sidecar()
    image_meta = _read_image_meta_sidecar()

    hidden = {str(name) for name in folder_state.get("hidden", []) if str(name)}
    raw_display_names = folder_state.get("display_names", {})
    if not isinstance(raw_display_names, dict):
        raw_display_names = {}
    display_names = {
        str(key): str(value or "").strip()
        for key, value in raw_display_names.items()
        if str(value or "").strip()
    }

    try:
        with transaction() as conn:
            folder_count = int(conn.execute(text("SELECT COUNT(*) FROM project_folder_metadata")).scalar() or 0)
            if folder_count == 0:
                for folder_name in sorted(set(folder_meta) | hidden | set(display_names)):
                    conn.execute(
                        text(
                            """
                            INSERT INTO project_folder_metadata
                                (folder_name, description, hidden, display_name)
                            VALUES (:folder_name, :description, :hidden, :display_name)
                            """
                        ),
                        {
                            "folder_name": folder_name,
                            "description": str(folder_meta.get(folder_name) or ""),
                            "hidden": 1 if folder_name in hidden else 0,
                            "display_name": display_names.get(folder_name) or None,
                        },
                    )

            file_count = int(conn.execute(text("SELECT COUNT(*) FROM project_file_metadata")).scalar() or 0)
            if file_count == 0:
                for folder_name, filename, value in _iter_file_meta_rows(file_meta):
                    conn.execute(
                        text(
                            """
                            INSERT INTO project_file_metadata (folder_name, filename, metadata)
                            VALUES (:folder_name, :filename, :metadata)
                            """
                        ),
                        {
                            "folder_name": folder_name,
                            "filename": filename,
                            "metadata": json.dumps(value, ensure_ascii=False),
                        },
                    )

            image_count = int(conn.execute(text("SELECT COUNT(*) FROM project_image_metadata")).scalar() or 0)
            if image_count == 0:
                for filename, value in _iter_image_meta_rows(image_meta):
                    conn.execute(
                        text(
                            """
                            INSERT INTO project_image_metadata (filename, metadata)
                            VALUES (:filename, :metadata)
                            """
                        ),
                        {
                            "filename": filename,
                            "metadata": json.dumps(value, ensure_ascii=False),
                        },
                    )
    except Exception as exc:
        _mark_db_unavailable(exc)


def _db_folder_rows() -> list[dict[str, Any]]:
    if not _db_available:
        return []
    _backfill_sidecars_to_db_once()
    if not _db_available:
        return []
    try:
        with transaction() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT folder_name, description, hidden, display_name
                    FROM project_folder_metadata
                    """
                )
            ).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        _mark_db_unavailable(exc)
        return []


def read_folder_meta() -> dict[str, str]:
    meta = _read_folder_meta_sidecar()
    for row in _db_folder_rows():
        meta[str(row["folder_name"])] = str(row.get("description") or "")
    return meta


def write_folder_meta(meta: dict[str, str]) -> None:
    if not _db_available:
        _write_folder_meta_sidecar(meta)
        return
    _backfill_sidecars_to_db_once()
    if not _db_available:
        _write_folder_meta_sidecar(meta)
        return
    try:
        with transaction() as conn:
            existing = {str(row["folder_name"]) for row in conn.execute(text("SELECT folder_name FROM project_folder_metadata")).mappings()}
            desired = set(meta.keys())
            for folder_name, description in meta.items():
                conn.execute(
                    text(
                        """
                        INSERT INTO project_folder_metadata (folder_name, description)
                        VALUES (:folder_name, :description)
                        ON DUPLICATE KEY UPDATE description = VALUES(description)
                        """
                    ),
                    {"folder_name": folder_name, "description": str(description or "")[:200]},
                )
            for folder_name in existing - desired:
                conn.execute(
                    text(
                        """
                        UPDATE project_folder_metadata
                        SET description = ''
                        WHERE folder_name = :folder_name
                        """
                    ),
                    {"folder_name": folder_name},
                )
    except Exception as exc:
        _mark_db_unavailable(exc)
        _write_folder_meta_sidecar(meta)
        return
    _write_folder_meta_sidecar(meta)


def read_folder_state() -> dict[str, object]:
    state = _read_folder_state_sidecar()
    hidden = set(state.get("hidden", []))
    display_names = dict(state.get("display_names", {}))
    for row in _db_folder_rows():
        folder_name = str(row["folder_name"])
        if row.get("hidden"):
            hidden.add(folder_name)
        elif folder_name in hidden:
            hidden.remove(folder_name)
        display_name = str(row.get("display_name") or "").strip()
        if display_name:
            display_names[folder_name] = display_name
        else:
            display_names.pop(folder_name, None)
    return {"hidden": sorted(hidden), "display_names": display_names}


def write_folder_state(state: dict[str, object]) -> None:
    hidden = {str(name) for name in state.get("hidden", []) if str(name)}
    raw_display_names = state.get("display_names", {})
    if not isinstance(raw_display_names, dict):
        raw_display_names = {}
    display_names = {
        str(key): str(value or "").strip()
        for key, value in raw_display_names.items()
        if str(value or "").strip()
    }
    if not _db_available:
        _write_folder_state_sidecar({"hidden": sorted(hidden), "display_names": display_names})
        return
    _backfill_sidecars_to_db_once()
    if not _db_available:
        _write_folder_state_sidecar({"hidden": sorted(hidden), "display_names": display_names})
        return
    try:
        folder_names = hidden | set(display_names.keys())
        with transaction() as conn:
            existing = {str(row["folder_name"]) for row in conn.execute(text("SELECT folder_name FROM project_folder_metadata")).mappings()}
            for folder_name in folder_names | existing:
                conn.execute(
                    text(
                        """
                        INSERT INTO project_folder_metadata (folder_name, hidden, display_name)
                        VALUES (:folder_name, :hidden, :display_name)
                        ON DUPLICATE KEY UPDATE
                            hidden = VALUES(hidden),
                            display_name = VALUES(display_name)
                        """
                    ),
                    {
                        "folder_name": folder_name,
                        "hidden": 1 if folder_name in hidden else 0,
                        "display_name": display_names.get(folder_name) or None,
                    },
                )
    except Exception as exc:
        _mark_db_unavailable(exc)
        _write_folder_state_sidecar({"hidden": sorted(hidden), "display_names": display_names})
        return
    _write_folder_state_sidecar({"hidden": sorted(hidden), "display_names": display_names})


def read_file_meta() -> dict[str, dict[str, Any]]:
    meta = _read_file_meta_sidecar()
    if not _db_available:
        return meta
    _backfill_sidecars_to_db_once()
    if not _db_available:
        return meta
    try:
        with transaction() as conn:
            rows = conn.execute(
                text("SELECT folder_name, filename, metadata FROM project_file_metadata")
            ).mappings().all()
        for row in rows:
            meta[f"{row['folder_name']}/{row['filename']}"] = _json_dict(row.get("metadata"))
    except Exception as exc:
        _mark_db_unavailable(exc)
    return meta


def write_file_meta(meta: dict[str, dict[str, Any]]) -> None:
    if not _db_available:
        _write_file_meta_sidecar(meta)
        return
    _backfill_sidecars_to_db_once()
    if not _db_available:
        _write_file_meta_sidecar(meta)
        return
    try:
        with transaction() as conn:
            conn.execute(text("DELETE FROM project_file_metadata"))
            for folder_name, filename, value in _iter_file_meta_rows(meta):
                conn.execute(
                    text(
                        """
                        INSERT INTO project_file_metadata (folder_name, filename, metadata)
                        VALUES (:folder_name, :filename, :metadata)
                        """
                    ),
                    {
                        "folder_name": folder_name,
                        "filename": filename,
                        "metadata": json.dumps(value, ensure_ascii=False),
                    },
                )
    except Exception as exc:
        _mark_db_unavailable(exc)
        _write_file_meta_sidecar(meta)
        return
    _write_file_meta_sidecar(meta)


def read_image_meta() -> dict[str, dict[str, Any]]:
    meta = _read_image_meta_sidecar()
    if not _db_available:
        return meta
    _backfill_sidecars_to_db_once()
    if not _db_available:
        return meta
    try:
        with transaction() as conn:
            rows = conn.execute(text("SELECT filename, metadata FROM project_image_metadata")).mappings().all()
        for row in rows:
            meta[str(row["filename"])] = _json_dict(row.get("metadata"))
    except Exception as exc:
        _mark_db_unavailable(exc)
    return meta


def write_image_meta(meta: dict[str, dict[str, Any]]) -> None:
    if not _db_available:
        _write_image_meta_sidecar(meta)
        return
    _backfill_sidecars_to_db_once()
    if not _db_available:
        _write_image_meta_sidecar(meta)
        return
    try:
        with transaction() as conn:
            conn.execute(text("DELETE FROM project_image_metadata"))
            for filename, value in _iter_image_meta_rows(meta):
                conn.execute(
                    text(
                        """
                        INSERT INTO project_image_metadata (filename, metadata)
                        VALUES (:filename, :metadata)
                        """
                    ),
                    {
                        "filename": filename,
                        "metadata": json.dumps(value, ensure_ascii=False),
                    },
                )
    except Exception as exc:
        _mark_db_unavailable(exc)
        _write_image_meta_sidecar(meta)
        return
    _write_image_meta_sidecar(meta)

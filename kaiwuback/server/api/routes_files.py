import base64
import json
import re
import shutil
from binascii import Error as BinasciiError
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from fastapi import Request
from fastapi.responses import JSONResponse, FileResponse
from starlette.responses import Response

from server.config import IMG_STORE, PROJECT_IMAGE_PREVIEW_STORE, PROJECT_LIB, PUBLIC_BASE_URL, public_url
from server.utils.file_io import (
    backfill_project_image_metadata_from_task_events,
    ensure_project_image_webp_preview,
    get_project_image_metadata_map,
    project_image_display_url,
    project_image_original_name_from_preview,
    project_image_original_url,
)

PROJECT_FOLDER_META = PROJECT_LIB / ".folder-meta.json"
PROJECT_FILE_META = PROJECT_LIB / ".file-meta.json"
PROJECT_FOLDER_STATE = PROJECT_LIB / ".folder-state.json"
VIRTUAL_PROJECT_FOLDERS = {"最近文件"}
DEFAULT_PROJECT_FOLDERS = {"编程文件库", "AI 对话产出", "创业资料", "产品设计", "营销素材"}
VIRTUAL_LIBRARY_FOLDERS = {"图片库", "视频库"}
INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _read_folder_meta() -> dict[str, str]:
    if not PROJECT_FOLDER_META.exists():
        return {}
    try:
        data = json.loads(PROJECT_FOLDER_META.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {str(key): str(value or "") for key, value in data.items()}
    except Exception as e:
        print(f"[FILE] Folder metadata read failed: {str(e)[:120]}", flush=True)
        return {}


def _write_folder_meta(meta: dict[str, str]) -> None:
    PROJECT_FOLDER_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_file_meta() -> dict[str, dict]:
    if not PROJECT_FILE_META.exists():
        return {}
    try:
        data = json.loads(PROJECT_FILE_META.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {str(key): value for key, value in data.items() if isinstance(value, dict)}
    except Exception as e:
        print(f"[FILE] File metadata read failed: {str(e)[:120]}", flush=True)
        return {}


def _write_file_meta(meta: dict[str, dict]) -> None:
    PROJECT_FILE_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_folder_state() -> dict[str, list[str]]:
    if not PROJECT_FOLDER_STATE.exists():
        return {"hidden": []}
    try:
        data = json.loads(PROJECT_FOLDER_STATE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"hidden": []}
        hidden = data.get("hidden", [])
        if not isinstance(hidden, list):
            hidden = []
        return {"hidden": [str(name) for name in hidden]}
    except Exception as e:
        print(f"[FILE] Folder state read failed: {str(e)[:120]}", flush=True)
        return {"hidden": []}


def _write_folder_state(state: dict[str, list[str]]) -> None:
    PROJECT_FOLDER_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _hide_virtual_folder(folder_name: str) -> None:
    state = _read_folder_state()
    hidden = set(state.get("hidden", []))
    hidden.add(folder_name)
    _write_folder_state({"hidden": sorted(hidden)})


def _show_folder(folder_name: str) -> None:
    state = _read_folder_state()
    hidden = set(state.get("hidden", []))
    if folder_name not in hidden:
        return
    hidden.remove(folder_name)
    _write_folder_state({"hidden": sorted(hidden)})


def _validate_leaf_name(name: str, label: str) -> tuple[str | None, JSONResponse | None]:
    clean_name = (name or "").strip()
    if not clean_name:
        return None, JSONResponse({"error": f"{label} required"}, status_code=400)
    if clean_name in {".", ".."} or "/" in clean_name or "\\" in clean_name:
        return None, JSONResponse({"error": f"invalid {label}"}, status_code=400)
    if INVALID_NAME_CHARS.search(clean_name):
        return None, JSONResponse({"error": f"invalid {label}"}, status_code=400)
    return clean_name, None


def _resolve_project_folder(folder_name: str):
    root = PROJECT_LIB.resolve()
    folder_path = (PROJECT_LIB / folder_name).resolve()
    if folder_path == root or root not in folder_path.parents:
        return None
    return folder_path


def _file_meta_key(folder_name: str, filename: str) -> str:
    return f"{folder_name}/{filename}"


def _infer_file_source(folder_name: str, filename: str, meta: dict[str, dict]) -> str:
    source = meta.get(_file_meta_key(folder_name, filename), {}).get("source")
    if source:
        return str(source)
    if folder_name == "AI 对话产出":
        return "ai"
    if folder_name not in DEFAULT_PROJECT_FOLDERS:
        return "manual_upload"
    return "system"


def _project_file_entry(folder_name: str, f, meta: dict[str, dict] | None = None):
    file_meta = meta or {}
    return {
        "name": f.name,
        "folder": folder_name,
        "type": f.suffix.upper().lstrip(".") or "FILE",
        "size": f.stat().st_size,
        "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "url": public_url(f"/project-files/{quote(folder_name, safe='')}/{quote(f.name, safe='')}"),
        "source": _infer_file_source(folder_name, f.name, file_meta),
    }


def _project_folder_entry(folder_path: Path, desc: str = "") -> dict:
    file_count = sum(1 for f in folder_path.iterdir() if f.is_file() and not f.name.startswith("."))
    return {
        "name": folder_path.name,
        "desc": desc,
        "count": f"{file_count} 个文件",
        "modified": datetime.fromtimestamp(folder_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "deletable": True,
    }


def _unique_file_path(folder_path, filename: str):
    candidate = folder_path / filename
    stem = candidate.stem
    suffix = candidate.suffix
    index = 1
    while candidate.exists():
        candidate = folder_path / f"{stem}_{index}{suffix}"
        index += 1
    return candidate


def _count_project_images() -> int:
    if not IMG_STORE.exists():
        return 0
    return sum(1 for f in IMG_STORE.iterdir() if f.is_file() and f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))


def _rewrite_folder_file_meta(old_folder: str, new_folder: str) -> None:
    meta = _read_file_meta()
    prefix = f"{old_folder}/"
    changed = False
    next_meta = {}
    for key, value in meta.items():
        if key.startswith(prefix):
            next_meta[f"{new_folder}/{key[len(prefix):]}"] = value
            changed = True
            continue
        next_meta[key] = value
    if changed:
        _write_file_meta(next_meta)


def _move_file_meta(old_folder: str, old_filename: str, new_folder: str, new_filename: str) -> dict[str, dict]:
    meta = _read_file_meta()
    old_key = _file_meta_key(old_folder, old_filename)
    new_key = _file_meta_key(new_folder, new_filename)
    if old_key in meta:
        meta[new_key] = meta.pop(old_key)
        _write_file_meta(meta)
    return meta


def _remove_file_meta(folder_name: str, filename: str) -> None:
    meta = _read_file_meta()
    key = _file_meta_key(folder_name, filename)
    if key not in meta:
        return
    meta.pop(key, None)
    _write_file_meta(meta)


def _rename_project_file(folder: str, filename: str, new_name: str):
    folder_name, folder_error = _validate_leaf_name(folder, "folder")
    if folder_error:
        return folder_error
    old_filename, old_filename_error = _validate_leaf_name(filename, "filename")
    if old_filename_error:
        return old_filename_error
    new_filename, new_filename_error = _validate_leaf_name(new_name, "filename")
    if new_filename_error:
        return new_filename_error

    folder_path = _resolve_project_folder(folder_name)
    if folder_path is None or not folder_path.is_dir():
        return JSONResponse({"error": "folder not found"}, status_code=404)
    old_path = folder_path / old_filename
    if not old_path.is_file():
        return JSONResponse({"error": "file not found"}, status_code=404)

    if old_filename != new_filename:
        new_path = folder_path / new_filename
        if new_path.exists():
            return JSONResponse({"error": "file already exists"}, status_code=409)
        try:
            old_path.rename(new_path)
        except Exception as e:
            print(f"[FILE] File rename failed: {str(e)[:120]}", flush=True)
            return JSONResponse({"error": "rename failed"}, status_code=500)
    else:
        new_path = old_path

    try:
        meta = _move_file_meta(folder_name, old_filename, folder_name, new_path.name)
    except Exception as e:
        print(f"[FILE] File metadata rename failed: {str(e)[:120]}", flush=True)
        meta = _read_file_meta()

    print(f"[FILE] File renamed: {folder_name}/{old_filename} -> {new_path.name}", flush=True)
    return {"status": "ok", "file": _project_file_entry(folder_name, new_path, meta)}


def _delete_project_file(folder: str, filename: str):
    folder_name, folder_error = _validate_leaf_name(folder, "folder")
    if folder_error:
        return folder_error
    safe_filename, filename_error = _validate_leaf_name(filename, "filename")
    if filename_error:
        return filename_error

    folder_path = _resolve_project_folder(folder_name)
    if folder_path is None or not folder_path.is_dir():
        return JSONResponse({"error": "folder not found"}, status_code=404)
    file_path = folder_path / safe_filename
    if not file_path.is_file():
        return JSONResponse({"error": "file not found"}, status_code=404)

    try:
        file_path.unlink()
    except Exception as e:
        print(f"[FILE] File delete failed: {str(e)[:120]}", flush=True)
        return JSONResponse({"error": "delete failed"}, status_code=500)

    try:
        _remove_file_meta(folder_name, safe_filename)
    except Exception as e:
        print(f"[FILE] File metadata cleanup failed: {str(e)[:120]}", flush=True)

    print(f"[FILE] File deleted: {folder_name}/{safe_filename}", flush=True)
    return {"status": "ok", "folder": folder_name, "filename": safe_filename}


LOCAL_IMAGE_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _matches_public_base_url(parsed) -> bool:
    public_base = urlparse(PUBLIC_BASE_URL)
    return bool(
        parsed.netloc
        and public_base.scheme
        and public_base.netloc
        and parsed.scheme == public_base.scheme
        and parsed.netloc == public_base.netloc
    )


def _attachment_headers(filename: str) -> dict[str, str]:
    fallback = "".join(
        ch if 32 <= ord(ch) < 127 and ch not in {'"', "\\", ";"} else "_"
        for ch in filename
    ).strip() or "image.jpg"
    encoded = quote(filename, safe="")
    return {
        "Content-Disposition": (
            f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{encoded}'
        )
    }


def _project_image_path_from_url(url: str) -> Path | None:
    parsed = urlparse(url)
    is_local_project_image = (
        parsed.path.startswith("/project-images/")
        and (not parsed.netloc or parsed.hostname in LOCAL_IMAGE_HOSTS or _matches_public_base_url(parsed))
    )
    if not is_local_project_image:
        return None

    filename = unquote(parsed.path.removeprefix("/project-images/"))
    if not filename:
        return None

    root = IMG_STORE.resolve()
    image_path = (root / filename).resolve()
    try:
        image_path.relative_to(root)
    except ValueError:
        return None
    return image_path


def _project_image_preview_path_from_url(url: str) -> Path | None:
    parsed = urlparse(url)
    is_local_project_image_preview = (
        parsed.path.startswith("/project-image-previews/")
        and (not parsed.netloc or parsed.hostname in LOCAL_IMAGE_HOSTS or _matches_public_base_url(parsed))
    )
    if not is_local_project_image_preview:
        return None

    filename = unquote(parsed.path.removeprefix("/project-image-previews/"))
    if not filename:
        return None

    root = PROJECT_IMAGE_PREVIEW_STORE.resolve()
    preview_path = (root / filename).resolve()
    try:
        preview_path.relative_to(root)
    except ValueError:
        return None
    return preview_path


def _project_image_original_path_from_preview_url(url: str) -> Path | None:
    preview_path = _project_image_preview_path_from_url(url)
    if preview_path is None:
        return None

    original_filename = project_image_original_name_from_preview(preview_path.name)
    if not original_filename:
        return None

    root = IMG_STORE.resolve()
    image_path = (root / original_filename).resolve()
    try:
        image_path.relative_to(root)
    except ValueError:
        return None
    return image_path


def register_file_routes(app):
    """向 FastAPI app 注册文件/图片相关路由"""

    @app.get("/api/project-images")
    def api_list_project_images():
        images = []
        if IMG_STORE.exists():
            image_files = [
                f for f in sorted(IMG_STORE.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
                if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
            ]
            image_metadata = get_project_image_metadata_map()
            ai_generated_image_files = [f for f in image_files if f.name.startswith("AI生图")]
            missing_metadata = any(
                not all(image_metadata.get(f.name, {}).get(field) for field in ("prompt", "model", "ratio", "resolution"))
                for f in ai_generated_image_files
            )
            if missing_metadata:
                backfill_project_image_metadata_from_task_events()
                image_metadata = get_project_image_metadata_map()
            for f in image_files:
                metadata = image_metadata.get(f.name, {})
                display_url = project_image_display_url(f.name)
                original_url = project_image_original_url(f.name)
                images.append({
                    **metadata,
                    "name": f.name,
                    "url": display_url,
                    "original_url": original_url,
                    "preview_url": display_url,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                })
        return images[:50]

    @app.get("/project-images/{filename:path}")
    def serve_project_image(filename: str):
        path = IMG_STORE / filename
        if path.exists():
            return FileResponse(path)
        return JSONResponse({"error": "not found"}, status_code=404)

    @app.get("/project-image-previews/{filename:path}")
    def serve_project_image_preview(filename: str):
        root = PROJECT_IMAGE_PREVIEW_STORE.resolve()
        path = (root / filename).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            return JSONResponse({"error": "not found"}, status_code=404)
        if path.exists():
            return FileResponse(path)

        original_filename = project_image_original_name_from_preview(path.name)
        if original_filename:
            original_path = (IMG_STORE.resolve() / original_filename).resolve()
            try:
                original_path.relative_to(IMG_STORE.resolve())
            except ValueError:
                original_path = None
            if original_path is not None and original_path.exists():
                preview_path = ensure_project_image_webp_preview(original_path)
                if preview_path is not None and preview_path.exists():
                    return FileResponse(preview_path)
        return JSONResponse({"error": "not found"}, status_code=404)

    @app.get("/api/project-files")
    def api_list_project_files(folder: str = ""):
        files = []
        meta = _read_file_meta()
        requested_folder = folder.strip()
        if PROJECT_LIB.exists():
            folders = []
            if requested_folder:
                folder_name, folder_error = _validate_leaf_name(requested_folder, "folder")
                if folder_error:
                    return folder_error
                folder_path = _resolve_project_folder(folder_name)
                if folder_path is None or not folder_path.is_dir():
                    return JSONResponse({"error": "folder not found"}, status_code=404)
                folders = [folder_path]
            else:
                folders = [item for item in PROJECT_LIB.iterdir() if item.is_dir()]

            for folder_path in folders:
                if folder_path.name.startswith("."):
                    continue
                for f in sorted(folder_path.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                    if f.is_file() and not f.name.startswith("."):
                        files.append((f.stat().st_mtime, _project_file_entry(folder_path.name, f, meta)))
        files.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in files]

    @app.get("/api/project-folders")
    def api_list_project_folders():
        folders = []
        meta = _read_folder_meta()
        hidden_folders = set(_read_folder_state().get("hidden", []))
        if PROJECT_LIB.exists():
            for folder in sorted(PROJECT_LIB.iterdir(), key=lambda x: x.name):
                if not folder.is_dir() or folder.name.startswith(".") or folder.name in VIRTUAL_PROJECT_FOLDERS or folder.name in hidden_folders:
                    continue
                file_count = sum(1 for f in folder.iterdir() if f.is_file() and not f.name.startswith("."))
                folders.append({
                    "name": folder.name,
                    "desc": meta.get(folder.name, ""),
                    "count": f"{file_count} 个文件",
                    "modified": datetime.fromtimestamp(folder.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "deletable": True,
                })
        folder_names = {folder["name"] for folder in folders}
        if "图片库" not in hidden_folders and "图片库" not in folder_names:
            folders.append({
                "name": "图片库",
                "desc": "",
                "count": f"{_count_project_images()} 个文件",
                "modified": datetime.fromtimestamp(IMG_STORE.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if IMG_STORE.exists() else "",
                "deletable": True,
            })
        if "视频库" not in hidden_folders and "视频库" not in folder_names:
            folders.append({
                "name": "视频库",
                "desc": "",
                "count": "0 个文件",
                "modified": "",
                "deletable": True,
            })
        return folders

    @app.post("/api/project-folders")
    async def api_create_project_folder(request: Request):
        data = await request.json()
        folder_name, error = _validate_leaf_name(data.get("name", ""), "folder name")
        if error:
            return error
        if folder_name in VIRTUAL_PROJECT_FOLDERS:
            return JSONResponse({"error": "folder name is reserved"}, status_code=400)
        folder_path = _resolve_project_folder(folder_name)
        if folder_path is None:
            return JSONResponse({"error": "invalid folder name"}, status_code=400)
        if folder_path.exists():
            return JSONResponse({"error": "folder already exists"}, status_code=409)

        folder_path.mkdir(parents=True, exist_ok=False)
        try:
            _show_folder(folder_name)
        except Exception as e:
            print(f"[FILE] Folder state update failed: {str(e)[:120]}", flush=True)
        desc = str(data.get("desc", "") or "").strip()
        if desc:
            meta = _read_folder_meta()
            meta[folder_name] = desc[:200]
            try:
                _write_folder_meta(meta)
            except Exception as e:
                print(f"[FILE] Folder metadata write failed: {str(e)[:120]}", flush=True)
        print(f"[FILE] Folder created: {folder_name}", flush=True)
        return {
            "status": "ok",
            "folder": {
                "name": folder_name,
                "desc": desc[:200],
                "count": "0 个文件",
                "modified": datetime.fromtimestamp(folder_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            },
        }

    @app.patch("/api/project-folders/{folder:path}")
    async def api_rename_project_folder(folder: str, request: Request):
        data = await request.json()
        old_name, old_error = _validate_leaf_name(folder, "folder name")
        if old_error:
            return old_error
        new_name, new_error = _validate_leaf_name(data.get("name", ""), "folder name")
        if new_error:
            return new_error
        if new_name in VIRTUAL_PROJECT_FOLDERS:
            return JSONResponse({"error": "folder name is reserved"}, status_code=400)

        folder_path = _resolve_project_folder(old_name)
        if folder_path is None or not folder_path.is_dir():
            return JSONResponse({"error": "folder not found"}, status_code=404)

        old_meta = _read_folder_meta()
        desc = str(data.get("desc", old_meta.get(old_name, "")) or "").strip()[:200]

        if old_name != new_name:
            new_path = _resolve_project_folder(new_name)
            if new_path is None:
                return JSONResponse({"error": "invalid folder name"}, status_code=400)
            if new_path.exists():
                return JSONResponse({"error": "folder already exists"}, status_code=409)
            try:
                folder_path.rename(new_path)
                folder_path = new_path
            except Exception as e:
                print(f"[FILE] Folder rename failed: {str(e)[:120]}", flush=True)
                return JSONResponse({"error": "rename failed"}, status_code=500)

        folder_meta = _read_folder_meta()
        folder_meta.pop(old_name, None)
        if desc:
            folder_meta[new_name] = desc
        try:
            _write_folder_meta(folder_meta)
        except Exception as e:
            print(f"[FILE] Folder metadata rename failed: {str(e)[:120]}", flush=True)

        if old_name != new_name:
            try:
                _rewrite_folder_file_meta(old_name, new_name)
            except Exception as e:
                print(f"[FILE] File metadata folder rename failed: {str(e)[:120]}", flush=True)
            try:
                state = _read_folder_state()
                hidden = set(state.get("hidden", []))
                if old_name in hidden:
                    hidden.remove(old_name)
                    hidden.add(new_name)
                    _write_folder_state({"hidden": sorted(hidden)})
            except Exception as e:
                print(f"[FILE] Folder state rename failed: {str(e)[:120]}", flush=True)

        print(f"[FILE] Folder renamed: {old_name} -> {new_name}", flush=True)
        return {"status": "ok", "folder": _project_folder_entry(folder_path, desc)}

    @app.delete("/api/project-folders/{folder:path}")
    def api_delete_project_folder(folder: str):
        folder_name, error = _validate_leaf_name(folder, "folder name")
        if error:
            return error

        folder_path = _resolve_project_folder(folder_name)
        deleted_physical_folder = False
        if folder_path is not None and folder_path.is_dir():
            try:
                shutil.rmtree(folder_path)
                deleted_physical_folder = True
            except Exception as e:
                print(f"[FILE] Folder delete failed: {str(e)[:120]}", flush=True)
                return JSONResponse({"error": "delete failed"}, status_code=500)
        elif folder_name == "图片库":
            try:
                if IMG_STORE.exists():
                    shutil.rmtree(IMG_STORE)
                IMG_STORE.mkdir(parents=True, exist_ok=True)
                _hide_virtual_folder(folder_name)
            except Exception as e:
                print(f"[FILE] Image library delete failed: {str(e)[:120]}", flush=True)
                return JSONResponse({"error": "delete failed"}, status_code=500)
        elif folder_name == "视频库":
            try:
                _hide_virtual_folder(folder_name)
            except Exception as e:
                print(f"[FILE] Video library delete failed: {str(e)[:120]}", flush=True)
                return JSONResponse({"error": "delete failed"}, status_code=500)
        else:
            return JSONResponse({"error": "folder not found"}, status_code=404)

        if deleted_physical_folder and folder_name in VIRTUAL_LIBRARY_FOLDERS:
            try:
                _hide_virtual_folder(folder_name)
            except Exception as e:
                print(f"[FILE] Folder state cleanup failed: {str(e)[:120]}", flush=True)

        folder_meta = _read_folder_meta()
        if folder_name in folder_meta:
            folder_meta.pop(folder_name, None)
            try:
                _write_folder_meta(folder_meta)
            except Exception as e:
                print(f"[FILE] Folder metadata cleanup failed: {str(e)[:120]}", flush=True)

        file_meta = _read_file_meta()
        file_prefix = f"{folder_name}/"
        cleaned_file_meta = {key: value for key, value in file_meta.items() if not key.startswith(file_prefix)}
        if len(cleaned_file_meta) != len(file_meta):
            try:
                _write_file_meta(cleaned_file_meta)
            except Exception as e:
                print(f"[FILE] File metadata cleanup failed: {str(e)[:120]}", flush=True)

        print(f"[FILE] Folder deleted: {folder_name}", flush=True)
        return {"status": "ok", "folder": folder_name}

    @app.post("/api/project-library/upload")
    async def api_upload_project_library_file(request: Request):
        data = await request.json()
        folder_name, folder_error = _validate_leaf_name(data.get("folder", ""), "folder")
        if folder_error:
            return folder_error
        filename, filename_error = _validate_leaf_name(data.get("filename", ""), "filename")
        if filename_error:
            return filename_error

        folder_path = _resolve_project_folder(folder_name)
        if folder_path is None or not folder_path.is_dir():
            return JSONResponse({"error": "folder not found"}, status_code=404)

        content = data.get("content", "")
        if data.get("base64"):
            try:
                raw = base64.b64decode(str(content).split(",")[-1], validate=True)
            except (BinasciiError, ValueError):
                return JSONResponse({"error": "invalid file content"}, status_code=400)
        else:
            raw = str(content).encode("utf-8")

        if not raw:
            return JSONResponse({"error": "content required"}, status_code=400)

        file_path = _unique_file_path(folder_path, filename)
        file_path.write_bytes(raw)
        meta = _read_file_meta()
        meta[_file_meta_key(folder_name, file_path.name)] = {
            "source": "manual_upload",
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        try:
            _write_file_meta(meta)
        except Exception as e:
            print(f"[FILE] File metadata write failed: {str(e)[:120]}", flush=True)
        print(f"[FILE] Uploaded: {folder_name}/{file_path.name}", flush=True)
        return {"status": "ok", "file": _project_file_entry(folder_name, file_path, meta)}

    @app.patch("/api/project-files/{folder}/{filename}")
    async def api_rename_project_file(folder: str, filename: str, request: Request):
        data = await request.json()
        return _rename_project_file(folder, filename, data.get("name", ""))

    @app.patch("/api/project-files")
    async def api_rename_project_file_body(request: Request):
        data = await request.json()
        return _rename_project_file(data.get("folder", ""), data.get("filename", ""), data.get("name", ""))

    @app.delete("/api/project-files/{folder}/{filename}")
    def api_delete_project_file(folder: str, filename: str):
        return _delete_project_file(folder, filename)

    @app.delete("/api/project-files")
    async def api_delete_project_file_body(request: Request):
        data = await request.json()
        return _delete_project_file(data.get("folder", ""), data.get("filename", ""))

    @app.get("/project-files/{folder:path}/{filename:path}")
    def serve_project_file(folder: str, filename: str):
        folder_name, folder_error = _validate_leaf_name(folder, "folder")
        if folder_error:
            return folder_error
        safe_filename, filename_error = _validate_leaf_name(filename, "filename")
        if filename_error:
            return filename_error
        folder_path = _resolve_project_folder(folder_name)
        if folder_path is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        path = folder_path / safe_filename
        if path.exists():
            return FileResponse(path)
        return JSONResponse({"error": "not found"}, status_code=404)

    @app.get("/api/download-image")
    def api_download_image(url: str = ""):
        if not url:
            return JSONResponse({"error": "url required"}, status_code=400)

        parsed = urlparse(url)
        local_path = _project_image_original_path_from_preview_url(url) or _project_image_path_from_url(url)
        if local_path is not None:
            if not local_path.is_file():
                return JSONResponse({"error": "image not found"}, status_code=404)
            return FileResponse(local_path, headers=_attachment_headers(local_path.name))
        if not parsed.netloc or parsed.hostname in LOCAL_IMAGE_HOSTS or _matches_public_base_url(parsed):
            return JSONResponse({"error": "unsupported image url"}, status_code=400)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return JSONResponse({"error": "unsupported image url"}, status_code=400)

        try:
            import requests as req
            resp = req.get(url, timeout=30)
            resp.raise_for_status()
            filename = Path(unquote(parsed.path)).name or 'image.jpg'
            return Response(content=resp.content, media_type=resp.headers.get('content-type', 'image/jpeg'),
                            headers=_attachment_headers(filename))
        except Exception as e:
            return JSONResponse({"error": str(e)[:200]}, status_code=502)

    # ── 文件上传 API ──
    @app.post("/api/upload-file")
    async def api_upload_file(request: Request):
        from server.intent.recognizer import add_uploaded_file, _uploaded_files
        data = await request.json()
        filename = data.get('filename', 'unknown')
        content = data.get('content', '')
        is_base64 = data.get('base64', False)

        if is_base64 and filename.lower().endswith('.pdf'):
            try:
                raw = base64.b64decode(content)
                import PyPDF2, io as std_io
                reader = PyPDF2.PdfReader(std_io.BytesIO(raw))
                pages = []
                for page in reader.pages:
                    t = page.extract_text()
                    if t: pages.append(t)
                content = '\n'.join(pages)
                print(f"[UPLOAD] PDF parsed: {filename}, {len(pages)} pages, {len(content)} chars", flush=True)
            except Exception as e:
                print(f"[UPLOAD] PDF parse failed: {e}", flush=True)
                return JSONResponse({"error": f"PDF解析失败: {str(e)[:200]}"}, status_code=400)

        if not content.strip():
            return JSONResponse({"error": "content required"}, status_code=400)
        add_uploaded_file(filename, content)
        return {"status": "ok", "filename": filename, "file_count": len(_uploaded_files), "files": [fn for fn, _ in _uploaded_files]}

    @app.get("/api/uploaded-files")
    def api_list_uploaded_files():
        from server.intent.recognizer import _uploaded_files
        return {"files": [{"name": fn, "size": len(ct)} for fn, ct in _uploaded_files]}

    @app.delete("/api/uploaded-files")
    def api_clear_uploaded_files():
        from server.intent.recognizer import clear_uploaded_files
        clear_uploaded_files()
        return {"status": "ok"}

    @app.delete("/api/uploaded-files/{filename}")
    def api_remove_uploaded_file(filename: str):
        from server.intent.recognizer import _uploaded_files
        # 原地修改列表，避免 import 的引用失效
        to_keep = [(fn, ct) for fn, ct in _uploaded_files if fn != filename]
        _uploaded_files.clear()
        _uploaded_files.extend(to_keep)
        return {"status": "ok"}

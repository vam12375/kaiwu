"""文件管理与图片服务路由 —— 从 main.py 抽取"""
import base64
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from starlette.responses import Response

from server.config import IMG_STORE, PROJECT_LIB


def register_file_routes(app):
    """向 FastAPI app 注册文件/图片相关路由"""

    @app.get("/api/project-images")
    def api_list_project_images():
        images = []
        if IMG_STORE.exists():
            for f in sorted(IMG_STORE.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
                    images.append({
                        "name": f.name,
                        "url": f"http://localhost:5001/project-images/{f.name}",
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

    @app.get("/api/project-files")
    def api_list_project_files():
        files = []
        if PROJECT_LIB.exists():
            for folder in PROJECT_LIB.iterdir():
                if folder.is_dir():
                    for f in sorted(folder.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                        if f.suffix.lower() in ('.html', '.pdf', '.pptx', '.txt'):
                            files.append({
                                "name": f.name, "folder": folder.name,
                                "type": f.suffix.upper().lstrip('.'),
                                "size": f.stat().st_size,
                                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                                "url": f"http://localhost:5001/project-files/{quote(folder.name)}/{quote(f.name)}",
                            })
        return files[:100]

    @app.get("/project-files/{folder:path}/{filename:path}")
    def serve_project_file(folder: str, filename: str):
        path = PROJECT_LIB / folder / filename
        if path.exists():
            return FileResponse(path)
        return JSONResponse({"error": "not found"}, status_code=404)

    @app.get("/api/download-image")
    def api_download_image(url: str = ""):
        import io
        if not url:
            return JSONResponse({"error": "url required"}, status_code=400)
        try:
            import requests as req
            resp = req.get(url, timeout=30)
            resp.raise_for_status()
            filename = url.split('/')[-1].split('?')[0] or 'image.jpg'
            return Response(content=resp.content, media_type=resp.headers.get('content-type', 'image/jpeg'),
                            headers={"Content-Disposition": f"attachment; filename={filename}"})
        except Exception as e:
            return JSONResponse({"error": str(e)[:200]}, status_code=500)

    # ── 文件上传 API ──
    @app.post("/api/upload-file")
    async def api_upload_file(request):
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

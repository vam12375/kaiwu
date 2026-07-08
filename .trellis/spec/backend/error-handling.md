# Backend Error Handling

> How backend errors are represented, logged, returned, and streamed.

---

## API Error Responses

HTTP APIs currently return a JSON object with an `error` field and an appropriate status code.

Examples:

- `routes_tasks.py` returns `{"error": "message is required"}` with `400`.
- `routes_tasks.py` returns `{"error": "task not found"}` with `404`.
- `routes_files.py` returns `{"error": "url required"}` with `400`.
- `routes_conv.py` truncates unexpected save errors to 200 chars and returns `500`.

Use this format for new route errors:

```python
return JSONResponse({"error": "short human-readable message"}, status_code=400)
```

Keep error messages concise. Do not include API keys, request headers, full prompts, or uploaded file contents.

---

## Scenario: Image Download API

### 1. Scope / Trigger

- Trigger: any change to `GET /api/download-image`.
- This endpoint bridges frontend download buttons to local project images and optional remote image URLs.

### 2. Signatures

- `GET /api/download-image?url=<image-url>` -> image bytes as an attachment, or `{"error": "<message>"}`.
- Local WebP preview URLs use `/project-image-previews/<original-filename>.webp` and should download the matching original image when possible.

### 3. Contracts

- `url` is required.
- Local generated images must use `/project-images/<filename>` on `localhost`, `127.0.0.1`, `::1`, or a relative `/project-images/...` URL.
- Local generated image previews may use `/project-image-previews/<filename>.webp` on the same allowed origins.
- Local project images are read from `IMG_STORE` directly rather than fetched through HTTP.
- Preview URLs are mapped back to `IMG_STORE/<original-filename>` before returning the attachment.
- Attachment responses must use an ASCII-safe `Content-Disposition` header with `filename*` for non-ASCII names.

### 4. Validation & Error Matrix

- Missing `url` -> `400 {"error": "url required"}`.
- Unsupported or unsafe local URL -> `400 {"error": "unsupported image url"}`.
- Local project image missing -> `404 {"error": "image not found"}`.
- Local preview URL with missing original image -> `404 {"error": "image not found"}`.
- Remote image fetch failure -> `502 {"error": "<truncated upstream error>"}`.

### 5. Good/Base/Bad Cases

- Good: `http://localhost:5001/project-images/AI%E7%94%9F%E5%9B%BE_x.jpg` returns `200` with `filename*=UTF-8''...`.
- Good: `http://localhost:5001/project-image-previews/AI%E7%94%9F%E5%9B%BE_x.jpg.webp` returns the original `AI生图_x.jpg` attachment.
- Base: `http://localhost:5001/project-images/missing.jpg` returns `404`, not a server error.
- Bad: `http://localhost:5001/api/conversations` is rejected instead of being proxied as an image download.

### 6. Tests Required

- Smoke or integration test a non-ASCII local filename and assert status `200`, byte length, and `filename*=UTF-8''` in `Content-Disposition`.
- Smoke a local preview URL and assert the returned attachment filename is the original filename, not the `.webp` preview filename.
- Assert a missing local image returns `404`.
- Assert an invalid URL returns `400`.
- Run `python -m compileall kaiwuback/server`.

### 7. Wrong vs Correct

#### Wrong

```python
headers={"Content-Disposition": f"attachment; filename={filename}"}
```

#### Correct

```python
headers={
    "Content-Disposition": (
        f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_name}'
    )
}
```

---

## Task Runtime Failures

Task execution failures must be visible through task state and SSE events.

Local pattern in `server/agent/runtime.py`:

1. Catch unexpected task exceptions in `AgentRuntime.execute()`.
2. Truncate the message.
3. Update the task to `failed`.
4. Emit `error`.
5. Emit `done`.

This ordering matters because frontend code uses `error` to render failure content and `done` to end loading state.

---

## Partial Failure Patterns

Some work should fail without aborting the whole task:

- Image generation errors emit `image_error` and continue other image styles.
- SVG generation errors are printed and skipped per style.
- Report PDF conversion failures can still return an HTML save result.
- Project image refresh failures in the frontend are swallowed because they are secondary UI refreshes.

Use partial failure only for optional side effects. Core task failures still go through `failed -> error -> done`.

---

## Validation Patterns

Validate user input at the route or payload-builder boundary:

- Empty task message: reject in `routes_tasks.py`.
- Empty uploaded file content: reject in `routes_files.py`.
- Missing conversation rename title: reject in `routes_conv.py`.
- Image defaults are normalized in `context_builder.py`.

When adding fields to task payloads, normalize them in `server/agent/context_builder.py` rather than spreading ad hoc defaults across routes and runtime code.

---

## Cancellation

Cancellation is represented as task state plus events:

- `TaskService.cancel_task()` calls `EventStore.mark_cancelled()`.
- Runtime loops regularly call `_cancelled(task_id)`.
- Streaming code emits `cancelled` and `done` for cancelled terminal state.

Any long-running loop added to `AgentRuntime` must check cancellation between external calls and before expensive work.

---

## External Provider Errors

Provider wrappers raise runtime errors with provider name, status code, and truncated response text:

- `server/llm_client/router.py`
- `server/llm_client/seedream.py`

Do not catch provider errors in route modules. Let the runtime convert them into task events or user-facing fallback text.

---

## Common Mistakes

- Emitting `done` without an `error` event after a failed task.
- Returning raw exception strings that include secrets or full provider payloads.
- Treating image generation failures as whole-task failures.
- Adding direct JSON/SSE error shapes that do not match existing frontend reducers.
- Forgetting to set task status to `failed` or `cancelled` when terminal failure happens.

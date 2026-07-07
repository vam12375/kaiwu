# Fix AI Image Download

## Goal

Fix the 500 error when users download AI-generated images from the chat result card or project image library.

## Requirements

* Downloading a local `/project-images/...` image through `/api/download-image?url=...` must return the image as an attachment.
* Chinese or other non-ASCII generated image filenames must not break response headers.
* Existing image generation, project image listing, and static image serving behavior must remain unchanged.
* Keep the fix scoped to the download path.

## Acceptance Criteria

* [x] `/api/download-image?url=http://localhost:5001/project-images/<encoded generated image>` returns `200`.
* [x] The response includes a valid attachment `Content-Disposition` for non-ASCII filenames.
* [x] Missing local images return `404`, not `500`.
* [x] Invalid or unsupported download URLs return a client error instead of crashing.
* [x] Backend syntax check passes for the touched route module or full server where possible.

## Definition of Done

* Backend route updated with focused handling for local project images and safe filename headers.
* Verification performed with at least one non-ASCII project image filename.
* Existing unrelated files are left untouched.

## Technical Approach

Parse the requested URL in `api_download_image`. For localhost `/project-images/...` URLs, resolve the filename into `IMG_STORE` and return `FileResponse` directly with an RFC 5987-compatible `filename*` attachment header. Keep a fallback path for external image URLs, but sanitize/encode the attachment filename there as well.

## Decision (ADR-lite)

**Context**: The frontend calls `/api/download-image` with URLs returned by `/api/project-images`, which include AI-generated filenames with non-ASCII prefixes.

**Decision**: Handle local project images as first-class files and encode attachment filenames instead of forwarding raw Unicode into HTTP headers.

**Consequences**: Downloads no longer depend on the backend making an HTTP request to itself, and non-ASCII names work consistently. The route remains small and compatible with the existing frontend.

## Out of Scope

* Redesigning the image result UI.
* Changing how Seedream images are generated or archived.
* Refactoring unrelated task/SSE or conversation save flows.

## Technical Notes

* User observed `GET /api/download-image?url=http%3A%2F%2Flocalhost%3A5001%2Fproject-images%2FAI%E7%94%9F%E5%9B%BE_...jpg` returning `500`.
* Frontend download callers: `kaiwu/src/features/chat/ConversationPanel.tsx`, `kaiwu/src/features/layout/AppModals.tsx`.
* Backend route: `kaiwuback/server/api/routes_files.py`.
* Smoke test confirmed `200` for an existing non-ASCII generated image filename, `404` for a missing local image, and `400` for an invalid URL.
* `python -m compileall kaiwuback/server` passed.

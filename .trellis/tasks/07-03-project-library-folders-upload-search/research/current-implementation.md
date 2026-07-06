# Current Implementation Notes

- `kaiwu/src/App.tsx` owns project server state: `projectImages` and `realProjectFiles`.
- `kaiwu/src/features/layout/MainStage.tsx` renders the project library. Search is currently static placeholder text, and folders open a modal.
- `kaiwu/src/features/layout/AppModals.tsx` renders the project modals. New folder and upload forms are visual only. Upload has a decorative file-type button row requested for removal.
- `kaiwuback/server/api/routes_files.py` owns file/image routes. `/api/project-files` lists files under `PROJECT_LIB`, and `/api/upload-file` is for conversation context uploads, not project library persistence.
- `kaiwuback/server/config.py` creates default `PROJECT_LIB` folders on startup.

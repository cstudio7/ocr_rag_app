# Roadmap

Planned work for KnowledgeNet, roughly in priority order. Estimates are rough.

## 1. Stability and security (≈8 h)

- [ ] **Force a password change on first login** for the seeded admin account,
      and refuse to start with the placeholder `SECRET_KEY` when not in debug mode
- [ ] Add rate limiting / lockout on `/login`
- [ ] Make sure every JSON API endpoint (`/api/*`) has CSRF protection and role checks
- [ ] Validate uploads (real PDF magic bytes, size, page count) before indexing
- [ ] Replace deprecated `PyPDF2` with `pypdf`; replace `datetime.utcnow()`
- [ ] Remove the `sys.path.append(...)` hacks by making `backend` a proper package

## 2. Desktop app (≈6 h)

- [ ] Run Flask **in-process on a background thread** instead of spawning
      `python app.py`, which doesn't work inside a PyInstaller bundle
- [ ] Replace the fixed `time.sleep(8)` with a health-check poll so the window
      opens as soon as the server is ready
- [ ] Store user data in the OS app-data directory, not inside the bundle;
      exclude `backend/data/` from the PyInstaller `--add-data`
- [ ] Add the missing `app-icon.ico` / `.icns` and test the Windows build
- [ ] GitHub Actions job that builds the macOS and Windows artifacts on tag

## 3. Code structure (≈6 h)

- [ ] Split the 1,400-line `backend/app.py` into Flask blueprints:
      `auth`, `documents`, `folders`, `search`, `users`
- [ ] Application factory (`create_app()`) so tests can spin up isolated apps
- [ ] Move indexing into a background worker/queue with per-job progress
      (the current `/api/progress` is global)

## 4. Search quality and features (≈8 h)

- [ ] Filter search by folder / document
- [ ] Highlight matched text and open the PDF at the matching page
- [ ] Hybrid search (BM25 keyword + embeddings) for exact terms and codes
- [ ] Optional answer generation: summarise the top results into a short answer
      with citations (pluggable, off by default)
- [ ] Detect and skip duplicate uploads by file hash

## 5. Tests and tooling (≈4 h)

- [x] pytest suite for models, chunking and spelling correction
- [ ] Route tests for auth, upload, folders and user management
- [ ] Extraction tests with small generated PDFs (text and scanned)
- [x] CI running the test suite on every push
- [ ] Add `ruff` linting and pre-commit hooks

## 6. Packaging and docs (≈3 h)

- [ ] `Dockerfile` with Tesseract/Poppler preinstalled
- [ ] Screenshots / GIF in the README
- [ ] User guide for roles, folders and re-indexing

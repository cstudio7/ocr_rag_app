# KnowledgeNet: OCR-powered PDF knowledge base

KnowledgeNet turns a pile of PDFs, including scanned ones, into a searchable
personal knowledge base. Upload documents, organise them into folders, and
search them by meaning instead of exact keywords. It runs entirely on your
own machine, either in the browser or as a desktop app.

It is for students, researchers and small teams who collect lots of PDFs
(lecture notes, reports, papers, manuals) and need to find "that paragraph
about X" quickly, without sending documents to a cloud service.

## Features

- **Upload PDFs** (single or batch) with live indexing progress
- **Smart text extraction**: uses the embedded text layer when present
  (PyMuPDF / pdfplumber) and falls back to **OCR** (Tesseract + Poppler) for
  scanned pages
- **Semantic search** over document chunks using local
  [sentence-transformers](https://www.sbert.net/) embeddings stored in
  [ChromaDB](https://www.trychroma.com/)
- **Spelling correction** and search suggestions
- **Folders**: create, colour, move and re-index documents
- **User accounts and roles**: `viewer` (search), `uploader` (upload/manage
  documents), `admin` (manage users)
- **Desktop app**: a PyQt5 window wrapping the web UI, packaged with
  PyInstaller for macOS (`.dmg`) and Windows

## Built with

Python 3.11 · Flask · Flask-Login · Flask-WTF · SQLAlchemy (SQLite) ·
sentence-transformers (`all-MiniLM-L6-v2`) · ChromaDB · Tesseract OCR ·
Poppler · PyMuPDF · pdfplumber · PyQt5 / QtWebEngine · PyInstaller

## Project layout

```
.
├── backend/                 # Flask web application
│   ├── app.py               # Routes and JSON API (entry point)
│   ├── config.py            # Settings (read from environment / .env)
│   ├── models.py            # User, Folder, Document models
│   ├── forms.py             # Auth/profile forms
│   ├── core/
│   │   ├── extract.py       # PDF text extraction + OCR fallback
│   │   ├── embedding.py     # Chunking and embeddings
│   │   ├── indexer.py       # Caching and writing chunks to ChromaDB
│   │   └── search.py        # Semantic search, spelling, suggestions
│   ├── templates/           # Jinja2 pages
│   ├── static/              # CSS / JS
│   └── data/                # Runtime data: PDFs, DB, vector store (git-ignored)
├── desktop/                 # Desktop wrapper
│   ├── main.py              # PyQt5 window that starts the backend
│   ├── build.sh             # PyInstaller build (macOS .dmg / Windows .exe)
│   └── assets/
├── tests/                   # pytest suite
├── requirements.txt         # Backend dependencies
├── requirements-desktop.txt # + Qt and PyInstaller
├── requirements-dev.txt     # + test tools
├── .env.example             # Configuration template
└── ROADMAP.md               # Planned work
```

## Getting started

### 1. System dependencies

OCR needs Tesseract and Poppler:

| OS | Command |
|----|---------|
| macOS | `brew install tesseract poppler` |
| Ubuntu/Debian | `sudo apt install tesseract-ocr poppler-utils` |
| Windows | Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and [Poppler](https://github.com/oschwartz10612/poppler-windows/releases), then add both to `PATH` |

### 2. Python environment

```bash
git clone https://github.com/cstudio7/ocr_rag_app.git
cd ocr_rag_app
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then edit SECRET_KEY and the admin password
```

The first run downloads the `all-MiniLM-L6-v2` embedding model (~90 MB).

### 3. Run the web app

```bash
cd backend
python app.py
```

Open <http://127.0.0.1:9123> and sign in with the admin account from your
`.env` (`DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD`). If you don't set
these, the defaults are `admin` / `admin123`, so **change the password right
away**.

### 4. Run as a desktop app (optional)

```bash
pip install -r requirements-desktop.txt
python desktop/main.py
```

To build a distributable app:

```bash
cd desktop
./build.sh        # produces dist/ and KnowledgeNet.dmg on macOS
```

## Configuration

All settings live in `backend/config.py` and can be overridden with
environment variables or a `.env` file in the project root. See
[`.env.example`](.env.example).

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | placeholder | Flask session signing key (**set this**) |
| `FLASK_DEBUG` | `false` | Enable the Flask debugger/reloader |
| `FLASK_HOST` / `FLASK_PORT` | `127.0.0.1` / `9123` | Bind address |
| `DATABASE_URL` | `sqlite:///backend/data/app.db` | SQLAlchemy database URL |
| `DEFAULT_ADMIN_*` | `admin` / `admin123` | Admin account created on first run |

## Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests stub out the embedding model, ChromaDB and OCR libraries, so they
run in a few seconds without downloading models.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and known issues.

## Contributors

- Victor Godwin ([@cstudio7](https://github.com/cstudio7)): creator and maintainer
- Early development of the upload/manage pages, user management and
  categorisation was done together with a collaborator (see the git history).

## License

[MIT](LICENSE)

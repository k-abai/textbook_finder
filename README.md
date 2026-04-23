# Textbook Finder

A launchable and testable full-stack textbook search demo app.

## Project structure

- `frontend/`: React + Vite web app for searching textbook listings.
- `backend/`: FastAPI service with textbook search, download simulation, and library APIs.

## Prerequisites

- Node.js 20+
- Python 3.11+
- Internet access to `registry.npmjs.org` and `pypi.org` (or a correctly configured corporate proxy)

## Run the app locally

### 1) Start the backend API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend health check: <http://localhost:8000/health>

### 2) Start the frontend site

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open: <http://localhost:5173>

### Fast localhost fallback (no dependency install)

If `npm install` or `pip install` is blocked in your environment, you can still launch a dependency-free local site:

```bash
chmod +x scripts/run_localhost.sh
./scripts/run_localhost.sh 5173
```

This script:

- starts the normal Vite app when `frontend/node_modules` exists
- otherwise serves `offline_site/index.html` via Python's built-in HTTP server

Open: <http://localhost:5173>

## Troubleshooting startup issues

If `localhost` does not come up and installs fail with `403 Forbidden`, the app dependencies were not installed. This project requires both frontend (`npm`) and backend (`pip`) packages before either server can start.

### Quick dependency check

```bash
# backend
cd backend
python -c "import fastapi, uvicorn, pydantic, slowapi; print('backend deps ok')"

# frontend
cd ../frontend
npm ls --depth=0
```

### Proxy-related install failures (common in locked-down environments)

If you see errors like:

- `npm ERR! 403 Forbidden - GET https://registry.npmjs.org/...`
- `ProxyError(... Tunnel connection failed: 403 Forbidden)`

then your proxy settings are blocking package downloads.

You can either:

1. Ask your network/admin team to allow your proxy to reach `registry.npmjs.org` and `pypi.org`, or
2. Temporarily run installs without proxy environment variables:

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy npm_config_http_proxy npm_config_https_proxy

cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

After dependencies install successfully, restart:

```bash
# terminal 1
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# terminal 2
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

## Test the app

### Frontend tests

```bash
cd frontend
npm test
```

### Backend tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Build frontend

```bash
cd frontend
npm run build
```

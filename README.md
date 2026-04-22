# Textbook Finder

A launchable and testable full-stack textbook search demo app.

## Project structure

- `frontend/`: React + Vite web app for searching textbook listings.
- `backend/`: FastAPI service with textbook search, download simulation, and library APIs.

## Prerequisites

- Node.js 20+
- Python 3.11+

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

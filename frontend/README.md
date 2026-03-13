# AI BJJ Coach — Frontend

React (Vite + TypeScript) chat interface for the AI BJJ Coach.

## Setup

```bash
cd frontend
npm install
npm run dev
```

The app starts at `http://localhost:5173` by default.

The frontend expects the backend at `http://localhost:8000`. Start the backend **first** — see `../backend/README.md`.

## Build for production

```bash
npm run build
# Static files are output to dist/
```

## Configuration

- **API endpoint:** Hardcoded to `http://localhost:8000` during dev.  
  Edit `API_BASE` at the top of `src/App.tsx` to point elsewhere.
- **Starter prompts:** Edit `STARTER_PROMPTS` in `src/App.tsx`.

## Key files

| File | Purpose |
|------|---------|
| `src/App.tsx` | Entire chat UI — messages, input bar, demo links |
| `src/index.css` | Dark mat-themed stylesheet |
| `index.html` | HTML shell |

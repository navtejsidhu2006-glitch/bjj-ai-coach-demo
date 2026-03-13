# AI BJJ Coach Demo

An AI-powered Brazilian Jiu Jitsu coaching app. Athletes can:

- Chat directly with an AI coach about **opponent analysis**, **gameplanning**, and **technique advice**.
- Paste YouTube links to match footage — the coach asks structured questions about what you see.
- Receive a structured **opponent profile (JSON)** plus a natural-language gameplan with Plan A, Plan B, and Plan C.
- Get **visual demo links** for any technique the coach recommends.

Built with **FastAPI** (backend) and **React + Vite** (frontend).

---

## Quickstart

### 1. Clone

```bash
git clone https://github.com/<your-username>/bjj-ai-coach-demo.git
cd bjj-ai-coach-demo
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set your Anthropic API key (get one at https://console.anthropic.com)
export ANTHROPIC_API_KEY=sk-ant-...

uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`.  
Health check: `curl http://localhost:8000/health`

### 3. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Project Structure

```
bjj-ai-coach-demo/
├── README.md              ← This file
├── backend/
│   ├── main.py            ← FastAPI app (system prompt, /chat, demo library)
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
└── frontend/
    ├── src/
    │   ├── App.tsx        ← Entire chat UI
    │   └── index.css      ← Styling
    ├── index.html
    ├── package.json
    └── README.md
```

---

## How it works

1. **System prompt** — The backend prepends a detailed BJJ coach system prompt on every API call. The coach always asks clarifying questions before giving a gameplan.

2. **Opponent analysis** — The coach asks about the opponent's guard style, passing tendencies, favourite submissions, and ruleset. From your descriptions it generates a JSON opponent profile followed by natural-language analysis.

3. **Gameplans** — Every major reply ends with structured Plan A (step-by-step), Plan B (from bottom), and Plan C (top game fallback).

4. **Visual demos** — The backend scans the AI reply for ~25 technique keywords and appends YouTube demo links from a hardcoded library. Extend `DEMO_LIBRARY` in `backend/main.py` to add more.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |

---

## Extending

- **Add demo videos:** Edit `DEMO_LIBRARY` in `backend/main.py`.
- **Tune the coach personality:** Edit `SYSTEM_PROMPT` in `backend/main.py`.
- **Change the LLM:** Swap `claude_sonnet_4_6` for any Anthropic model in the `client.messages.create` call.

---

*Created with [Perplexity Computer](https://www.perplexity.ai/computer)*

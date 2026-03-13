# AI BJJ Coach — Backend

FastAPI server exposing a `/chat` endpoint that powers the BJJ Coach UI.

## Setup

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=sk-ant-...   # or use .env with python-dotenv

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Endpoints

| Method | Path      | Description                        |
|--------|-----------|------------------------------------|
| GET    | /health   | Liveness check                     |
| POST   | /chat     | Chat with the AI BJJ coach         |

### POST /chat

**Request body:**
```json
{
  "messages": [
    { "role": "user", "content": "I have a match against John Danaher's student..." }
  ]
}
```

**Response:**
```json
{
  "reply": "Before I build a gameplan, let me ask a few questions...",
  "demo_links": [
    { "technique": "Knee Cut Pass", "url": "https://youtube.com/..." }
  ]
}
```

## Configuration

- **LLM model:** `claude_sonnet_4_6` (Anthropic)
- **Technique library:** Hardcoded in `main.py` under `DEMO_LIBRARY` — add or edit entries freely.
- **System prompt:** Edit `SYSTEM_PROMPT` in `main.py` to customise coach behaviour.

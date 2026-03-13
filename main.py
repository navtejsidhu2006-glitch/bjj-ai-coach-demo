"""
main.py — AI BJJ Coach FastAPI backend.

Endpoints:
  GET  /health      — liveness check
  POST /chat        — forwards messages to the LLM with a BJJ coach system prompt

The LLM is accessed via the Anthropic Messages API (claude_sonnet_4_6).
Technique → demo-video mapping is injected into the AI reply when a keyword matches.
"""

from __future__ import annotations

import os
import re
from typing import List, Literal

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="AI BJJ Coach", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for local demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env

# ---------------------------------------------------------------------------
# BJJ Coach system prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an elite Brazilian Jiu Jitsu coach specialising in opponent scouting, \
competitive gameplanning, and technique instruction. Your athletes are serious competitors — treat \
them as such. Be direct, specific, and practical.

## Your coaching process

1. **Clarify before advising.** When a new scouting or gameplan request arrives, always ask for:
   - Ruleset (gi / no-gi / ADCC / points / submission-only / EBI / etc.)
   - The athlete's own A-game (what are their best positions and submissions?)
   - Opponent weight class, approximate skill level, and known competition record if available.
   Do NOT skip these questions on a first request about an opponent.

2. **YouTube / video links.** If the user pastes YouTube or video URLs, acknowledge them but \
explain you cannot watch them. Instead, ask the user to describe what happens in those matches \
(e.g., "What guard does the opponent play most? What passes does he chain? What are his favourite \
submission threats? How does he react when taken down?"). Use those descriptions as your \
primary scouting data.

3. **Opponent profile.** Once you have enough information, generate a structured opponent profile \
in this exact JSON block followed by a plain-English summary:

```json
{
  "name": "<opponent name or 'Unknown'>",
  "weight_class": "<weight>",
  "ruleset": "<ruleset>",
  "guard_style": "<e.g. Closed Guard, Lasso, De La Riva>",
  "passing_style": "<e.g. Torreando, Knee-cut, Leg-drag>",
  "favourite_submissions": ["<sub1>", "<sub2>"],
  "takedown_game": "<e.g. strong wrestling, weak takedowns>",
  "top_game": "<description>",
  "defensive_tendencies": "<description>",
  "key_danger_zones": ["<position1>", "<position2>"],
  "identified_weaknesses": ["<weakness1>", "<weakness2>"]
}
```

4. **Gameplan output.** End every major analytical reply with ALL of the following sections:

**PLAN A — Primary gameplan (step-by-step):**
• Step 1: ...
• Step 2: ...
• Step 3: ...
• Step 4: ...
• Step 5: ...

**PLAN B — If you end up on the bottom:**
• ...
• ...

**PLAN C — If you end up on top but can't pass:**
• ...
• ...

5. **Technique recommendations.** When you recommend a specific technique (e.g. "knee cut pass", \
"rear naked choke", "double leg"), name it clearly so the system can attach a visual demo link.

6. **Tone.** Be a demanding but supportive coach. Use plain language. No waffle. \
If you don't know something, say so and ask for more detail.
"""

# ---------------------------------------------------------------------------
# Technique → demo video URL mapping  (hardcoded library)
# ---------------------------------------------------------------------------

DEMO_LIBRARY: dict[str, str] = {
    "knee cut pass":          "https://www.youtube.com/watch?v=sY_eA4VNSTY",
    "knee slice":             "https://www.youtube.com/watch?v=sY_eA4VNSTY",
    "torreando pass":         "https://www.youtube.com/watch?v=sY_eA4VNSTY",
    "double leg":             "https://www.youtube.com/watch?v=HhP4kH0SRH0",
    "single leg":             "https://www.youtube.com/watch?v=HhP4kH0SRH0",
    "rear naked choke":       "https://www.youtube.com/watch?v=XDfJxiECE7s",
    "rnc":                    "https://www.youtube.com/watch?v=XDfJxiECE7s",
    "arm bar":                "https://www.youtube.com/watch?v=6AaLNJQPQbg",
    "armbar":                 "https://www.youtube.com/watch?v=6AaLNJQPQbg",
    "triangle choke":         "https://www.youtube.com/watch?v=XoLCM0zW3f8",
    "triangle":               "https://www.youtube.com/watch?v=XoLCM0zW3f8",
    "guillotine":             "https://www.youtube.com/watch?v=5B5M4MNPTYU",
    "berimbolo":              "https://www.youtube.com/watch?v=TRwpBGGgL_s",
    "de la riva":             "https://www.youtube.com/watch?v=p8J-qQOvI2c",
    "leg drag":               "https://www.youtube.com/watch?v=VknZG7NHFCM",
    "x guard":                "https://www.youtube.com/watch?v=HCIzPR5g2gY",
    "heel hook":              "https://www.youtube.com/watch?v=NhIFhNXoHcE",
    "outside heel hook":      "https://www.youtube.com/watch?v=NhIFhNXoHcE",
    "kneebar":                "https://www.youtube.com/watch?v=ZK1hFXFU-Oc",
    "back take":              "https://www.youtube.com/watch?v=KvJTQHAqaEY",
    "back control":           "https://www.youtube.com/watch?v=KvJTQHAqaEY",
    "mount":                  "https://www.youtube.com/watch?v=0F7kFKxuITk",
    "side control":           "https://www.youtube.com/watch?v=Yw3nUDj5JMc",
    "butterfly guard":        "https://www.youtube.com/watch?v=A4TxOXIhMfA",
    "closed guard":           "https://www.youtube.com/watch?v=gX8p8pKBPQo",
    "guard retention":        "https://www.youtube.com/watch?v=uSHlcjmEy_Y",
    "kimura":                 "https://www.youtube.com/watch?v=LL0LBHfQi8g",
    "americana":              "https://www.youtube.com/watch?v=TT-k5XAFuFk",
    "omoplata":               "https://www.youtube.com/watch?v=1b02r3BWTYI",
    "anaconda choke":         "https://www.youtube.com/watch?v=Z5KhlV8fqNg",
    "darce choke":            "https://www.youtube.com/watch?v=WZ8KHXPOHSE",
}

def find_demo_links(text: str) -> list[tuple[str, str]]:
    """Return (technique_name, url) pairs for any technique keywords found in the text."""
    text_lower = text.lower()
    found: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for keyword, url in DEMO_LIBRARY.items():
        # whole-word / phrase match
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower) and url not in seen_urls:
            found.append((keyword.title(), url))
            seen_urls.add(url)
    return found[:3]   # cap at 3 links per reply

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    reply: str
    demo_links: list[dict]   # [{"technique": "...", "url": "..."}]

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Forward the conversation to the LLM (prepending the BJJ coach system prompt)
    and return the assistant reply plus any matched demo-video links.
    """
    # Filter out any existing system messages from the client — we own the system prompt
    user_messages = [m for m in req.messages if m.role != "system"]

    if not user_messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    # Build the messages list for the Anthropic API
    anthropic_messages = [{"role": m.role, "content": m.content} for m in user_messages]

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=anthropic_messages,
        )
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"LLM API error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    reply_text: str = response.content[0].text

    # Inject demo links for any matched technique keywords
    links = find_demo_links(reply_text)
    demo_links = [{"technique": t, "url": u} for t, u in links]

    return ChatResponse(reply=reply_text, demo_links=demo_links)


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

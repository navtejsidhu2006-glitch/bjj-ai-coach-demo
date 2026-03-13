/**
 * App.tsx — AI BJJ Coach single-page chat UI.
 *
 * Architecture:
 *  - Messages array held in React state.
 *  - On send, full history is POST-ed to /chat.
 *  - Backend returns { reply, demo_links }.
 *  - Markdown rendered via react-markdown; URLs clickable.
 */

import { useState, useRef, useEffect, KeyboardEvent, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ── Backend URL ────────────────────────────────────────────────────────────
// __PORT_8000__ is replaced by the proxy path at deploy time.
// During local dev it stays as the literal string, so we fall back to localhost.
const API_BASE = "__PORT_8000__".startsWith("__")
  ? "http://localhost:8000"
  : "__PORT_8000__";

// ── Types ──────────────────────────────────────────────────────────────────
interface Message {
  role: "user" | "assistant";
  content: string;
  demo_links?: { technique: string; url: string }[];
  error?: boolean;
}

// ── Starter prompts (chips) ────────────────────────────────────────────────
const STARTER_PROMPTS = [
  "I have a tournament this weekend — help me scout my opponent",
  "What's the best gameplan against a leg-lock specialist?",
  "My opponent plays De La Riva guard, how do I pass?",
  "Walk me through a no-gi back-take gameplan",
];

// ── Logo SVG ───────────────────────────────────────────────────────────────
function Logo() {
  return (
    <svg
      className="header-logo"
      viewBox="0 0 34 34"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="BJJ Coach Logo"
    >
      {/* Circular mat / ring */}
      <circle cx="17" cy="17" r="15.5" stroke="#e8a020" strokeWidth="1.5" />
      {/* Two figures (simplified grappling silhouette) */}
      {/* Athlete 1 head */}
      <circle cx="11" cy="11" r="2.5" fill="#e8a020" />
      {/* Athlete 1 body curling forward */}
      <path d="M11 13.5 C11 17 15 18 17 21" stroke="#e8a020" strokeWidth="1.8" strokeLinecap="round" />
      {/* Athlete 2 head */}
      <circle cx="23" cy="23" r="2.5" fill="#f0f2f7" />
      {/* Athlete 2 body */}
      <path d="M23 20.5 C23 17 19 16 17 13" stroke="#f0f2f7" strokeWidth="1.8" strokeLinecap="round" />
      {/* Control grip indicator */}
      <circle cx="17" cy="17" r="1.5" fill="#e8a020" opacity="0.7" />
    </svg>
  );
}

// ── Typing indicator ───────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="message-row assistant">
      <div className="avatar coach">🥋</div>
      <div className="bubble">
        <div className="typing-indicator">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  );
}

// ── Single message ─────────────────────────────────────────────────────────
function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`} data-testid={`msg-${msg.role}`}>
      {!isUser && <div className="avatar coach">🥋</div>}
      <div className="bubble">
        {msg.error ? (
          <div className="error-banner">{msg.content}</div>
        ) : isUser ? (
          // User messages: plain text (no markdown needed)
          <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
        ) : (
          // Coach messages: full markdown
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
        )}
        {/* Demo video links injected by backend */}
        {msg.demo_links && msg.demo_links.length > 0 && (
          <div className="demo-links">
            <div className="demo-links-label">🎥 Visual Demos</div>
            {msg.demo_links.map((link) => (
              <a
                key={link.url}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="demo-link"
                data-testid={`demo-link-${link.technique.replace(/\s+/g, "-")}`}
              >
                ▶ {link.technique}
              </a>
            ))}
          </div>
        )}
      </div>
      {isUser && <div className="avatar user">🥊</div>}
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages]   = useState<Message[]>([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const messagesEndRef             = useRef<HTMLDivElement>(null);
  const textareaRef                = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom after every new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 180)}px`;
  };

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { role: "user", content: trimmed };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          // Send only user/assistant messages (no system); backend owns system prompt
          messages: nextMessages.map(({ role, content }) => ({ role, content })),
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }

      const data: { reply: string; demo_links: { technique: string; url: string }[] } = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply, demo_links: data.demo_links },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Something went wrong: ${msg}. Make sure the backend is running at ${API_BASE}.`,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [messages, loading]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (not Shift+Enter)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const canSend = input.trim().length > 0 && !loading;

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <Logo />
        <div>
          <div className="header-title">AI BJJ Coach</div>
          <div className="header-subtitle">Opponent scouting · Gameplanning · Technique advice</div>
        </div>
        <div className="header-status">
          <span className="status-dot" />
          Ready
        </div>
      </header>

      {/* ── Messages ── */}
      <main className="messages" role="log" aria-live="polite">
        {messages.length === 0 ? (
          /* Welcome / empty state */
          <div className="welcome">
            <div className="welcome-icon">🥋</div>
            <h2>Your BJJ Coach is Ready</h2>
            <p>
              Paste opponent footage links, describe what you see, and get structured
              gameplans with Plan A, Plan B, and technique demos.
            </p>
            <div className="welcome-chips">
              {STARTER_PROMPTS.map((p) => (
                <button
                  key={p}
                  className="chip"
                  data-testid="starter-chip"
                  onClick={() => sendMessage(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)
        )}
        {loading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </main>

      {/* ── Input bar ── */}
      <div className="input-bar">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Describe your opponent, paste a YouTube link, or ask a technique question…"
          rows={1}
          disabled={loading}
          data-testid="input-chat"
          aria-label="Chat input"
        />
        <button
          className="send-btn"
          onClick={() => sendMessage(input)}
          disabled={!canSend}
          data-testid="button-send"
          aria-label="Send message"
        >
          Send ↑
        </button>
      </div>

      {/* ── Footer ── */}
      <footer className="footer">
        <a href="https://www.perplexity.ai/computer" target="_blank" rel="noopener noreferrer">
          Created with Perplexity Computer
        </a>
      </footer>
    </div>
  );
}

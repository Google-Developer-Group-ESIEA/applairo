// components/Chat.tsx
// Composant client : gère l'état de la conversation et l'interaction utilisateur.
// La logique réseau vit dans lib/api ; l'extraction du profil dans lib/profile.

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

import { sendMessage, startSession } from "@/lib/api";
import { extractProfile } from "@/lib/profile";
import type { ChatMessage } from "@/lib/types";
import ProfilePanel from "./ProfilePanel";

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const profile = useMemo(() => extractProfile(messages), [messages]);

  // Ouverture d'une session ADK au montage + message d'accueil de l'agent.
  useEffect(() => {
    let cancelled = false;
    startSession()
      .then(({ session_id, reply }) => {
        if (cancelled) return;
        setSessionId(session_id);
        setMessages([{ role: "assistant", content: reply }]);
      })
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, []);

  // Auto-scroll vers le dernier message.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !sessionId || loading) return;

    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const { reply } = await sendMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="layout">
      <section className="chat">
        <header className="chat-header">
          <h1>Applairo</h1>
          <p>GDG ESIEA · Google ADK + Gemini 2.5 Flash + Adzuna</p>
        </header>

        <div className="messages" ref={scrollRef}>
          {messages.map((m, i) => (
            <div key={i} className={`bubble bubble-${m.role}`}>
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
          ))}
          {loading && (
            <div className="bubble bubble-assistant bubble-typing">
              <span />
              <span />
              <span />
            </div>
          )}
        </div>

        {error && <div className="error">{error}</div>}

        <form className="composer" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              sessionId ? "Tapez votre message..." : "Connexion à l'agent..."
            }
            disabled={!sessionId || loading}
          />
          <button type="submit" disabled={!sessionId || loading || !input.trim()}>
            Envoyer
          </button>
        </form>
      </section>

      <ProfilePanel profile={profile} />
    </div>
  );
}

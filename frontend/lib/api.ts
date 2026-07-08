// lib/api.ts
// Client HTTP côté navigateur. Appelle les route handlers Next (/api/**), qui
// relaient vers le backend. Le composant Chat ne connaît que ces fonctions.

import type { ChatResponse, StartSessionResponse } from "./types";

export async function startSession(): Promise<StartSessionResponse> {
  const res = await fetch("/api/sessions", { method: "POST" });
  if (!res.ok) throw new Error("Impossible de créer la session.");
  return res.json();
}

export async function sendMessage(
  sessionId: string,
  message: string,
): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error("Erreur lors de l'envoi du message.");
  return res.json();
}

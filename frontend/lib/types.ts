// lib/types.ts
// Types partagés côté frontend. Reflètent les DTOs de l'API backend.

export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface StartSessionResponse {
  session_id: string;
  reply: string;
}

export interface ChatResponse {
  reply: string;
}

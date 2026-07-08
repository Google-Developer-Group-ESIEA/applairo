// lib/api.ts
// Client HTTP côté navigateur. Appelle les route handlers Next (/api/**), qui
// relaient vers le backend. Les composants ne connaissent que ces fonctions.

import type { SearchProfile, SearchResponse } from "./types";

async function readError(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    if (data?.detail) return String(data.detail);
  } catch {
    // corps non-JSON : on retombe sur le message par défaut
  }
  return fallback;
}

export async function analyzeCv(file: File): Promise<SearchProfile> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/cv", { method: "POST", body: form });
  if (!res.ok) {
    throw new Error(await readError(res, "Analyse du CV impossible."));
  }
  return res.json();
}

export async function search(profile: SearchProfile): Promise<SearchResponse> {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    throw new Error(await readError(res, "Recherche impossible."));
  }
  return res.json();
}

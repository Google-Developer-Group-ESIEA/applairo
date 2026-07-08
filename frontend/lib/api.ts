// lib/api.ts
// Client HTTP côté navigateur. Appelle les route handlers Next (/api/**), qui
// relaient vers le backend. Les composants ne connaissent que ces fonctions.

import type { SearchEvent, SearchProfile, SearchResponse } from "./types";

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

// Cadence « premium » : délai MINIMUM (ms) entre deux événements AFFICHÉS.
//
// CHOIX PRODUIT, purement côté UI : le backend, lui, émet tout à sa vitesse
// réelle (le flux reste honnête). Le fan-out et la sélection sont quasi
// instantanés ; sans plancher ils défileraient en un éclair. Le comité, à
// l'inverse, arrive déjà espacé de plusieurs secondes (temps réel des appels
// LLM) : le plancher ne fait que garantir un minimum, il ne RETARDE jamais un
// événement au-delà de son arrivée réelle (on prend max(arrivée, créneau)).
const PACING_MS: Record<SearchEvent["type"], number> = {
  queries: 350,
  query_done: 450, // remplissage séquentiel et posé des barres de recherche
  merged: 700, // un temps avant l'entonnoir de sélection
  committee_start: 600, // un temps avant l'apparition des experts
  member_done: 500, // plancher ; les vrais écarts du comité dominent
  result: 800, // un temps après la dernière carte avant de basculer
  error: 0, // les erreurs s'affichent sans délai
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Variante en flux : /api/search/stream renvoie du NDJSON (une ligne JSON par
// avancement). On lit le corps au fil de l'eau avec un reader et on cadence
// l'affichage via `onEvent` (voir PACING_MS). `pace: false` = vitesse réelle.
//
// On n'utilise PAS EventSource : c'est un POST avec corps, qu'EventSource ne sait
// pas porter. fetch + reader gère POST + lecture incrémentale.
export async function searchStream(
  profile: SearchProfile,
  onEvent: (event: SearchEvent) => void,
  opts?: { pace?: boolean },
): Promise<void> {
  const pace = opts?.pace ?? true;
  const res = await fetch("/api/search/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok || !res.body) {
    throw new Error(await readError(res, "Recherche impossible."));
  }

  // Révèle un événement en respectant le créneau minimum. Attendre ici laisse les
  // événements suivants dans le tampon réseau : ils seront lus juste après.
  let nextAllowed = 0;
  const emit = async (event: SearchEvent) => {
    if (pace) {
      const now = Date.now();
      const revealAt = Math.max(now, nextAllowed);
      if (revealAt > now) await sleep(revealAt - now);
      onEvent(event);
      nextAllowed = Date.now() + PACING_MS[event.type];
    } else {
      onEvent(event);
    }
  };

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const flushLines = async (final: boolean) => {
    // Un chunk réseau peut couper une ligne en deux, ou en contenir plusieurs :
    // on ne traite que les lignes complètes et on garde le reste en tampon.
    let nl: number;
    while ((nl = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      if (line) await emit(JSON.parse(line) as SearchEvent);
    }
    if (final) {
      const tail = buffer.trim();
      if (tail) await emit(JSON.parse(tail) as SearchEvent);
    }
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    await flushLines(false);
  }
  await flushLines(true);
}

// lib/progress.ts
// État d'avancement d'une recherche, reconstruit à partir du flux d'événements
// NDJSON. Isolé ici (hors composant) pour rester simple à suivre et à tester :
// `initialProgress` + `applyEvent` forment un petit réducteur pur.

import type { SearchEvent, Usage } from "./types";

export interface ProgressState {
  queries: { title: string; location: string }[];
  // Nombre d'offres par requête terminée, clé `${title}@@${location}`.
  queryCounts: Record<string, number>;
  found: number; // total courant d'offres remontées par le fan-out
  merged: { found: number; unique: number; kept: number } | null;
  members: string[];
  membersDone: Record<string, number>; // membre -> nombre d'offres notées
  // Consommation par membre (tokens + coût), affichée dès qu'il a fini.
  memberUsage: Record<string, Usage>;
  offers: number; // offres envoyées au comité
}

export const initialProgress: ProgressState = {
  queries: [],
  queryCounts: {},
  found: 0,
  merged: null,
  members: [],
  membersDone: {},
  memberUsage: {},
  offers: 0,
};

// Applique un événement du flux à l'état (immutable). Les événements terminaux
// `result` / `error` ne touchent pas l'avancement : ils sont gérés par l'appelant.
export function applyEvent(state: ProgressState, event: SearchEvent): ProgressState {
  switch (event.type) {
    case "queries":
      return { ...state, queries: event.queries };
    case "query_done":
      return {
        ...state,
        queryCounts: {
          ...state.queryCounts,
          [`${event.title}@@${event.location}`]: event.count,
        },
        found: state.found + event.count,
      };
    case "merged":
      return {
        ...state,
        merged: { found: event.found, unique: event.unique, kept: event.kept },
      };
    case "committee_start":
      return { ...state, members: event.members, offers: event.offers };
    case "member_done": {
      const membersDone = { ...state.membersDone, [event.member]: event.count };
      // Les champs de consommation sont optionnels : on n'enregistre l'usage que
      // si le backend l'a fourni pour ce membre.
      if (event.cost_usd === undefined || event.total_tokens === undefined) {
        return { ...state, membersDone };
      }
      return {
        ...state,
        membersDone,
        memberUsage: {
          ...state.memberUsage,
          [event.member]: {
            model: event.model ?? "",
            prompt_tokens: event.prompt_tokens ?? 0,
            output_tokens: event.output_tokens ?? 0,
            total_tokens: event.total_tokens,
            cost_usd: event.cost_usd,
          },
        },
      };
    }
    default:
      return state;
  }
}

// lib/progress.ts
// État d'avancement d'une recherche, reconstruit à partir du flux d'événements
// NDJSON. Isolé ici (hors composant) pour rester simple à suivre et à tester :
// `initialProgress` + `applyEvent` forment un petit réducteur pur.

import type { SearchEvent } from "./types";

export interface ProgressState {
  queries: { title: string; location: string }[];
  // Nombre d'offres par requête terminée, clé `${title}@@${location}`.
  queryCounts: Record<string, number>;
  found: number; // total courant d'offres remontées par le fan-out
  merged: { found: number; unique: number; kept: number } | null;
  members: string[];
  membersDone: Record<string, number>; // membre -> nombre d'offres notées
  offers: number; // offres envoyées au comité
}

export const initialProgress: ProgressState = {
  queries: [],
  queryCounts: {},
  found: 0,
  merged: null,
  members: [],
  membersDone: {},
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
    case "member_done":
      return {
        ...state,
        membersDone: { ...state.membersDone, [event.member]: event.count },
      };
    default:
      return state;
  }
}

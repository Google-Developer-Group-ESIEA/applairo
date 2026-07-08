// lib/types.ts
// Types partagés côté frontend. Reflètent les DTOs de l'API backend (V2).

export interface SearchProfile {
  titles: string[];
  locations: string[];
  level: string;
  contract_type: string;
}

export interface CommitteeScore {
  member: string;
  score: number;
  notes: string;
}

export interface Job {
  title: string;
  company: string;
  location: string;
  url: string;
  salary_min: number | null;
  salary_max: number | null;
}

export interface ScoredJob {
  job: Job;
  scores: CommitteeScore[];
  overall: number;
}

export interface SearchResponse {
  jobs: ScoredJob[];
}

// Événements du flux NDJSON de /api/search/stream. Le champ `type` discrimine
// l'étape ; ils reflètent 1:1 ce qu'émet le backend (application/progress.py).
export type SearchEvent =
  | { type: "queries"; queries: { title: string; location: string }[] }
  | { type: "query_done"; title: string; location: string; count: number }
  | { type: "merged"; found: number; unique: number; kept: number }
  | { type: "committee_start"; members: string[]; offers: number }
  | { type: "member_done"; member: string; count: number }
  | { type: "error"; detail: string }
  | { type: "result"; jobs: ScoredJob[] };

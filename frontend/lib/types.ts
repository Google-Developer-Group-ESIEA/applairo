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

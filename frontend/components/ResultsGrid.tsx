// components/ResultsGrid.tsx
// Etape 6 : la grille de resultats. Chaque offre est une carte structuree
// (JobCard) ; plus de bloc de texte a parser. Les offres arrivent deja triees
// par note globale decroissante (cote backend).

import type { ScoredJob } from "@/lib/types";

import JobCard from "./JobCard";

interface Props {
  jobs: ScoredJob[];
  onReset: () => void;
}

export default function ResultsGrid({ jobs, onReset }: Props) {
  return (
    <section className="results">
      <div className="results-head">
        <h2 className="card-title">
          {jobs.length} offre{jobs.length > 1 ? "s" : ""} evaluee
          {jobs.length > 1 ? "s" : ""} par le comite
        </h2>
        <button className="btn-secondary" onClick={onReset}>
          Nouveau CV
        </button>
      </div>

      {jobs.length === 0 ? (
        <p className="empty">
          Aucune offre trouvee. Revenez en arriere et elargissez les intitules ou
          les localisations.
        </p>
      ) : (
        <div className="results-grid">
          {jobs.map((scored) => (
            <JobCard key={scored.job.url} scored={scored} />
          ))}
        </div>
      )}
    </section>
  );
}

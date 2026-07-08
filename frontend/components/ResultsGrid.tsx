// components/ResultsGrid.tsx
// Etape 6 : la grille de resultats. Chaque offre est une carte structuree
// (JobCard) ; plus de bloc de texte a parser. Les offres arrivent deja triees
// par note globale decroissante (cote backend).

import type { ScoredJob } from "@/lib/types";

import JobCard from "./JobCard";

interface Props {
  jobs: ScoredJob[];
  onRefine: () => void;
  onNewCv: () => void;
}

export default function ResultsGrid({ jobs, onRefine, onNewCv }: Props) {
  return (
    <section className="results">
      <div className="results-head">
        <h2 className="card-title">
          {jobs.length} offre{jobs.length > 1 ? "s" : ""} évaluée
          {jobs.length > 1 ? "s" : ""} par le comité
        </h2>
        <div className="results-actions">
          <button className="btn-secondary" onClick={onRefine}>
            Affiner la recherche
          </button>
          <button className="btn-secondary" onClick={onNewCv}>
            Nouveau CV
          </button>
        </div>
      </div>

      {jobs.length === 0 ? (
        <p className="empty">
          Aucune offre trouvée. Affinez la recherche pour élargir les intitulés ou
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

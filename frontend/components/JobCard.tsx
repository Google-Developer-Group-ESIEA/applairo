// components/JobCard.tsx
// Une offre evaluee : entete (poste, entreprise, salaire), note globale, et le
// detail par membre du comite (RH / Tech lead / Marche) avec sa justification.

import type { ScoredJob } from "@/lib/types";

function scoreClass(score: number): string {
  if (score >= 70) return "score-high";
  if (score >= 40) return "score-mid";
  return "score-low";
}

function formatSalary(min: number | null, max: number | null): string | null {
  const fmt = (n: number) => n.toLocaleString("fr-FR");
  if (min && max) return `${fmt(min)} - ${fmt(max)} €/an`;
  if (min) return `À partir de ${fmt(min)} €/an`;
  return null;
}

export default function JobCard({ scored }: { scored: ScoredJob }) {
  const { job, scores, overall } = scored;
  const salary = formatSalary(job.salary_min, job.salary_max);

  return (
    <article className="job-card">
      <div className="job-card-head">
        <div className={`overall ${scoreClass(overall)}`}>
          <span className="overall-value">{overall}</span>
          <span className="overall-label">/ 100</span>
        </div>
        <div className="job-card-title">
          <h3>{job.title}</h3>
          <p className="job-company">{job.company}</p>
          <p className="job-meta">
            {job.location || "Lieu non précisé"}
            {salary ? ` - ${salary}` : ""}
          </p>
        </div>
      </div>

      <ul className="committee">
        {scores.map((s) => (
          <li key={s.member} className="committee-item">
            <div className="committee-head">
              <span className="committee-member">{s.member}</span>
              <span className={`committee-score ${scoreClass(s.score)}`}>
                {s.score}
              </span>
            </div>
            <p className="committee-notes">{s.notes}</p>
          </li>
        ))}
      </ul>

      <a className="btn-secondary job-link" href={job.url} target="_blank" rel="noreferrer">
        Voir l&apos;offre
      </a>
    </article>
  );
}

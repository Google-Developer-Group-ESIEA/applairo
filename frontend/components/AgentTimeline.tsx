// components/AgentTimeline.tsx
// Affichage TEMPS RÉEL du travail des agents pendant une recherche (étape 5).
//
// Chaque phase reflète un événement réellement reçu du backend (flux NDJSON) :
//   1. Recherche des offres : une barre par requête, remplie dès qu'elle revient.
//   2. Sélection : l'entonnoir trouvées -> uniques -> retenues.
//   3. Comité : une ligne par expert. Le vrai temps de calcul vit ici (3 appels
//      LLM parallèles, ~15 s) ; on l'habille de mots de « réflexion » qui tournent
//      (à la Claude Code) pendant que chaque expert délibère. Les experts sont
//      réellement en train de travailler : seuls les mots sont du décor.

"use client";

import { useEffect, useState } from "react";

import type { ProgressState } from "@/lib/progress";

// Sous-titre + initiales par membre du comité. Les clés doivent correspondre
// EXACTEMENT aux noms émis par le backend (avec accents : « Marché »).
const MEMBER_META: Record<string, { role: string; initials: string }> = {
  RH: { role: "Culture, ton et mots-clés du CV", initials: "RH" },
  "Tech lead": { role: "Crédibilité technique du profil", initials: "TL" },
  "Marché": { role: "Réalisme et attractivité de l'offre", initials: "M" },
};

// Mots de réflexion qui défilent pendant qu'un expert délibère (pur décor).
const THINKING_WORDS = [
  "Réflexion…",
  "Lecture des offres…",
  "Analyse du profil…",
  "Pondération des critères…",
  "Recoupement…",
  "Délibération…",
  "Cogitation…",
  "Évaluation…",
];

type PhaseStatus = "idle" | "active" | "done";

function Phase({
  index,
  title,
  status,
  children,
}: {
  index: number;
  title: string;
  status: PhaseStatus;
  children?: React.ReactNode;
}) {
  return (
    <div className={`phase phase-${status}`}>
      <div className="phase-rail">
        <span className="phase-marker">{status === "done" ? "" : index}</span>
      </div>
      <div className="phase-body">
        <p className="phase-title">{title}</p>
        {children}
      </div>
    </div>
  );
}

// Étiquette « en réflexion » : fait tourner les mots tant qu'elle est montée.
// `seed` décale le mot de départ pour que les experts ne soient pas synchrones.
function ThinkingLabel({ seed }: { seed: number }) {
  const [i, setI] = useState(seed % THINKING_WORDS.length);
  useEffect(() => {
    const id = setInterval(
      () => setI((v) => (v + 1) % THINKING_WORDS.length),
      1900,
    );
    return () => clearInterval(id);
  }, []);
  return (
    <span className="thinking">
      <span className="agent-thinking" aria-hidden>
        <i />
        <i />
        <i />
      </span>
      <span key={i} className="thinking-word">
        {THINKING_WORDS[i]}
      </span>
    </span>
  );
}

export default function AgentTimeline({
  progress,
  finalizing = false,
  finalizingMs = 1800,
}: {
  progress: ProgressState;
  finalizing?: boolean;
  finalizingMs?: number;
}) {
  const { queries, queryCounts, found, merged, members, membersDone, offers } =
    progress;

  const fanoutTotal = queries.length;
  const fanoutDone = Object.keys(queryCounts).length;
  const fanoutComplete = fanoutTotal > 0 && fanoutDone >= fanoutTotal;
  const committeeDone =
    members.length > 0 && members.every((m) => m in membersDone);

  const searchStatus: PhaseStatus = fanoutComplete ? "done" : "active";
  const mergeStatus: PhaseStatus = merged
    ? "done"
    : fanoutComplete
      ? "active"
      : "idle";
  const committeeStatus: PhaseStatus =
    members.length === 0 ? "idle" : committeeDone ? "done" : "active";

  const keyOf = (title: string, location: string) => `${title}@@${location}`;

  return (
    <section className="timeline card">
      <p className="timeline-lead">
        Les agents travaillent sur votre profil. Suivez leur avancée en direct.
      </p>

      <Phase index={1} title="Recherche des offres" status={searchStatus}>
        <div className="query-rows">
          {queries.map((q) => {
            const k = keyOf(q.title, q.location);
            const done = k in queryCounts;
            return (
              <div key={k} className="query-row">
                <span className="query-row-label">
                  {q.title}
                  <span className="query-row-loc">{q.location}</span>
                </span>
                <span className={`qbar${done ? " qbar-done" : ""}`}>
                  {done ? (
                    <span className="qbar-fill" />
                  ) : (
                    <span className="qbar-slide" />
                  )}
                </span>
                <span className="query-row-count">
                  {done ? queryCounts[k] : ""}
                </span>
              </div>
            );
          })}
        </div>
        {fanoutTotal > 0 && (
          <p className="phase-meta">{found} offres trouvées</p>
        )}
      </Phase>

      <Phase index={2} title="Sélection des meilleures" status={mergeStatus}>
        {merged && (
          <div className="merge-flow">
            <span className="merge-stat">
              <strong>{merged.found}</strong>trouvées
            </span>
            <span className="merge-arrow" aria-hidden />
            <span className="merge-stat">
              <strong>{merged.unique}</strong>uniques
            </span>
            <span className="merge-arrow" aria-hidden />
            <span className="merge-stat merge-stat-final">
              <strong>{merged.kept}</strong>retenues
            </span>
          </div>
        )}
      </Phase>

      <Phase
        index={3}
        title={
          members.length > 0
            ? `Le comité délibère sur ${offers} offres`
            : "Le comité délibère"
        }
        status={committeeStatus}
      >
        {members.length > 0 && (
          <div className="experts">
            {members.map((m, idx) => {
              const done = m in membersDone;
              const meta = MEMBER_META[m] ?? { role: "", initials: m.slice(0, 2) };
              return (
                <div
                  key={m}
                  className={`expert-row${done ? " expert-row-done" : ""}`}
                >
                  <span className="agent-avatar">{meta.initials}</span>
                  <div className="expert-main">
                    <div className="expert-id">
                      <p className="agent-name">{m}</p>
                      <p className="agent-role">{meta.role}</p>
                    </div>
                    <div className="expert-status">
                      {done ? (
                        <span className="agent-done">
                          {membersDone[m]} offres notées
                        </span>
                      ) : (
                        <ThinkingLabel seed={idx} />
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Phase>

      {finalizing && (
        <div className="finalizing" role="status">
          <p className="finalizing-text">
            Classement finalisé, ouverture de vos résultats…
          </p>
          <div className="finalizing-bar">
            <span
              className="finalizing-fill"
              style={{ animationDuration: `${finalizingMs}ms` }}
            />
          </div>
        </div>
      )}
    </section>
  );
}

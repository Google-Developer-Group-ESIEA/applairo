// components/ProfilePanel.tsx
// Panneau pédagogique « Profil en cours de collecte ».
// Composant de présentation pur : reçoit un Profile, n'a aucun état propre.

import { PROFILE_STEPS, type Profile } from "@/lib/profile";

export default function ProfilePanel({ profile }: { profile: Profile }) {
  const total = PROFILE_STEPS.length;
  const collected = Object.values(profile).filter(Boolean).length;
  const progress = Math.round((collected / total) * 100);
  const complete = collected === total;

  return (
    <aside className="panel">
      <h2 className="panel-title">Profil en cours de collecte</h2>

      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${progress}%` }} />
      </div>
      <p className="progress-label">
        {collected}/{total} informations collectées
      </p>

      <ul className="steps">
        {PROFILE_STEPS.map((step) => {
          const value = profile[step.key];
          return (
            <li key={step.key} className={`step ${value ? "step-done" : ""}`}>
              <span className="step-label">{step.label}</span>
              <span className="step-value">
                {value ?? <em>En attente...</em>}
              </span>
            </li>
          );
        })}
      </ul>

      {complete && (
        <div className="step-complete">Recherche lancée !</div>
      )}

      <div className="panel-note">
        <h3>Comment ça marche ?</h3>
        <ol>
          <li>L&apos;agent pose 4 questions pour construire votre profil.</li>
          <li>Chaque réponse s&apos;affiche ici en temps réel.</li>
          <li>
            Profil complet, l&apos;agent appelle l&apos;outil{" "}
            <code>search_jobs</code>.
          </li>
          <li>L&apos;outil interroge l&apos;API Adzuna et renvoie les offres.</li>
        </ol>
      </div>
    </aside>
  );
}

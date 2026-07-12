// components/SearchFlow.tsx
// Orchestrateur client du pipeline, organise en trois ONGLETS librement
// navigables : CV -> Recherche -> Resultats.
//
// Il detient tout l'etat (profil editable, resultats) ; les sous-composants
// restent presentationnels. Comme le profil vit ici, on peut :
//   - revenir sur un onglet sans perdre ses modifications (#1)
//   - relancer une recherche depuis le CV existant en ajustant les parametres,
//     sans re-uploader (#2)
//
// Un onglet ne devient accessible qu'une fois son prerequis obtenu (Recherche
// apres analyse du CV, Resultats apres une recherche), puis reste navigable.

"use client";

import { useState } from "react";

import { analyzeCv, searchStream } from "@/lib/api";
import { applyEvent, initialProgress, type ProgressState } from "@/lib/progress";
import type { ScoredJob, SearchProfile, Usage } from "@/lib/types";

import AgentTimeline from "./AgentTimeline";
import ProfileForm from "./ProfileForm";
import ResultsGrid from "./ResultsGrid";
import Uploader from "./Uploader";
import UsagePill from "./UsagePill";

type Tab = "cv" | "search" | "results";

// Temps d'attente affiché (avec indication) entre la fin du comité et la bascule
// vers les résultats : évite une redirection brutale, laisse voir le classement
// se finaliser. La barre d'indication est animée sur cette même durée.
const REDIRECT_DELAY_MS = 1800;

// Analyse du CV : durée mini affichée (ressenti "premium"), défilée sur 3 étapes
// de 1,5 s chacune, quelle que soit la vitesse réelle du backend.
const CV_PHASES = 3;
const CV_LOAD_MS = 4500;

const sleep = (ms: number): Promise<void> =>
  new Promise((r) => setTimeout(r, ms));

export default function SearchFlow() {
  const [tab, setTab] = useState<Tab>("cv");
  const [profile, setProfile] = useState<SearchProfile | null>(null);
  // Consommation de l'appel d'extraction du profil (1er des 4 appels du cycle).
  const [profileUsage, setProfileUsage] = useState<Usage | null>(null);
  const [cvName, setCvName] = useState<string | null>(null);
  const [jobs, setJobs] = useState<ScoredJob[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Vrai pendant la pause "finalisation" juste avant la bascule vers les résultats.
  const [finalizing, setFinalizing] = useState(false);
  // Étape courante d'analyse du CV (0..CV_PHASES-1), pendant l'upload.
  const [cvPhase, setCvPhase] = useState(0);
  // Avancement de la recherche. Non nul pendant le run ET après : la frise reste
  // montée dans l'onglet Recherche une fois le pipeline terminé (trace du travail
  // des agents). On ne le remet à zéro qu'au lancement d'une nouvelle recherche
  // ou à l'arrivée d'un nouveau CV.
  const [progress, setProgress] = useState<ProgressState | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setCvPhase(0);
    // Fait défiler les étapes (Téléchargement / Extraction / Analyse) sur une
    // durée fixe. Purement visuel : la vraie analyse tourne en parallèle.
    const step = CV_LOAD_MS / CV_PHASES;
    const timers = [
      setTimeout(() => setCvPhase(1), step),
      setTimeout(() => setCvPhase(2), step * 2),
    ];
    try {
      // On attend le résultat ET la durée mini : l'affichage ne file jamais en
      // dessous de CV_LOAD_MS. Si l'analyse échoue, Promise.all rejette aussitôt.
      const [deduced] = await Promise.all([analyzeCv(file), sleep(CV_LOAD_MS)]);
      setProfile(deduced.profile);
      setProfileUsage(deduced.usage);
      setCvName(file.name);
      setJobs(null); // les anciens resultats ne correspondent plus au nouveau CV
      setProgress(null); // ... la frise de l'ancien CV non plus
      setTab("search");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      timers.forEach(clearTimeout);
      setBusy(false);
      setCvPhase(0);
    }
  }

  async function runSearch() {
    if (!profile) return;
    setBusy(true);
    setError(null);
    setJobs(null);
    setProgress(initialProgress);
    try {
      let finalJobs: ScoredJob[] | null = null;
      let streamError: string | null = null;
      await searchStream(profile, (event) => {
        if (event.type === "result") {
          finalJobs = event.jobs;
        } else if (event.type === "error") {
          streamError = event.detail;
        } else {
          // Étapes intermédiaires : on met à jour l'avancement affiché.
          setProgress((prev) => (prev ? applyEvent(prev, event) : prev));
        }
      });
      if (streamError) throw new Error(streamError);
      setJobs(finalJobs ?? []);
      // Pause "finalisation" : le comité vient de finir, on laisse un temps avec
      // une indication avant de basculer, plutôt qu'une redirection sèche.
      setFinalizing(true);
      await sleep(REDIRECT_DELAY_MS);
      setTab("results");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      setFinalizing(false);
      // La frise reste montée : on ne remet pas `progress` à null ici.
    }
  }

  const tabs: { id: Tab; label: string; enabled: boolean }[] = [
    { id: "cv", label: "CV", enabled: true },
    { id: "search", label: "Recherche", enabled: profile !== null },
    { id: "results", label: "Résultats", enabled: jobs !== null },
  ];

  return (
    <main className="flow">
      <a href="/comment-ca-marche" className="btn-secondary hiw-corner">
        Comment ça marche ?
      </a>
      <header className="flow-header">
        <h1 className="brand">ApplaiNow</h1>
        <p className="tagline">
          Votre CV, analysé et confronté à de vraies offres par un comité d&apos;agents.
        </p>
        <nav className="tabs">
          {tabs.map((t, i) => (
            <button
              key={t.id}
              type="button"
              className={`tab${t.id === tab ? " tab-active" : ""}`}
              disabled={!t.enabled || busy}
              onClick={() => setTab(t.id)}
            >
              <span className="tab-index">{i + 1}</span>
              <span className="tab-label">{t.label}</span>
            </button>
          ))}
        </nav>
      </header>

      {error && <p className="error">{error}</p>}

      {tab === "cv" && (
        <Uploader
          onSelect={handleFile}
          busy={busy}
          currentName={cvName}
          phase={cvPhase}
        />
      )}
      {/* Onglet Recherche : le formulaire, puis la frise des agents qui reste
          montée pendant ET après la recherche (trace du travail des agents). */}
      {tab === "search" && profile && (
        <>
          <ProfileForm
            profile={profile}
            busy={busy}
            hasResults={jobs !== null}
            onChange={setProfile}
            onSearch={runSearch}
          />
          {progress && (
            <AgentTimeline
              progress={progress}
              finalizing={finalizing}
              finalizingMs={REDIRECT_DELAY_MS}
            />
          )}
        </>
      )}
      {tab === "results" && jobs && (
        <ResultsGrid
          jobs={jobs}
          onRefine={() => setTab("search")}
          onNewCv={() => setTab("cv")}
        />
      )}

      {/* Pastille de consommation : hors des onglets, visible partout, se remplit
          au fil de l'eau (profil puis comité). */}
      <UsagePill profileUsage={profileUsage} progress={progress} />
    </main>
  );
}

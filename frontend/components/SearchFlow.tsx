// components/SearchFlow.tsx
// Orchestrateur client du pipeline en 3 etapes : depot du CV -> ajustement du
// profil -> resultats. Detient tout l'etat et les appels reseau ; les sous-
// composants restent presentationnels.
//
// Le pipeline backend etant SANS ETAT, c'est ce composant qui conserve le profil
// (issu de l'analyse du CV) et le renvoie tel quel a l'etape recherche.

"use client";

import { useState } from "react";

import { analyzeCv, search } from "@/lib/api";
import type { ScoredJob, SearchProfile } from "@/lib/types";

import ProfileForm from "./ProfileForm";
import ResultsGrid from "./ResultsGrid";
import Uploader from "./Uploader";

type Stage = "upload" | "profile" | "results";

const STEPS = ["Deposer le CV", "Ajuster la recherche", "Resultats"];

export default function SearchFlow() {
  const [stage, setStage] = useState<Stage>("upload");
  const [profile, setProfile] = useState<SearchProfile | null>(null);
  const [jobs, setJobs] = useState<ScoredJob[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const deduced = await analyzeCv(file);
      setProfile(deduced);
      setStage("profile");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSearch(edited: SearchProfile) {
    setBusy(true);
    setError(null);
    setProfile(edited);
    try {
      const res = await search(edited);
      setJobs(res.jobs);
      setStage("results");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setStage("upload");
    setProfile(null);
    setJobs([]);
    setError(null);
  }

  const activeStep = stage === "upload" ? 0 : stage === "profile" ? 1 : 2;

  return (
    <main className="flow">
      <header className="flow-header">
        <h1 className="brand">Applairo</h1>
        <p className="tagline">
          Votre CV, analyse et confronte a de vraies offres par un comite d&apos;agents.
        </p>
        <ol className="stepper">
          {STEPS.map((label, i) => (
            <li
              key={label}
              className={`step${i === activeStep ? " step-active" : ""}${
                i < activeStep ? " step-done" : ""
              }`}
            >
              <span className="step-index">{i + 1}</span>
              <span className="step-label">{label}</span>
            </li>
          ))}
        </ol>
      </header>

      {error && <p className="error">{error}</p>}

      {stage === "upload" && <Uploader onSelect={handleFile} busy={busy} />}
      {stage === "profile" && profile && (
        <ProfileForm initial={profile} busy={busy} onSearch={handleSearch} />
      )}
      {stage === "results" && <ResultsGrid jobs={jobs} onReset={reset} />}
    </main>
  );
}

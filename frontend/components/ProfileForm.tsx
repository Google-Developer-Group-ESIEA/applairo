// components/ProfileForm.tsx
// Onglet "Recherche" : l'utilisateur ajuste le profil deduit du CV (ajoute/retire
// des intitules et des localisations, change le niveau et le contrat) puis lance
// - ou relance - la recherche.
//
// Composant CONTROLE : l'etat du profil vit dans SearchFlow, pas ici. On peut
// donc naviguer vers un autre onglet et revenir sans perdre ses modifications,
// et relancer une recherche depuis le CV existant en ajustant les parametres.

"use client";

import { useState } from "react";

import type { SearchProfile } from "@/lib/types";

const LEVELS = ["junior", "intermédiaire", "senior"];
const CONTRACTS = ["", "CDI", "CDD", "stage", "alternance"];

interface Props {
  profile: SearchProfile;
  busy: boolean;
  hasResults: boolean;
  onChange: (profile: SearchProfile) => void;
  onSearch: () => void;
}

export default function ProfileForm({
  profile,
  busy,
  hasResults,
  onChange,
  onSearch,
}: Props) {
  const { titles, locations, level, contract_type: contract } = profile;

  // Le modele peut deduire une valeur hors des listes fixes (ex: niveau
  // "confirme", contrat "freelance"). Un <select> controle dont la valeur n'est
  // dans aucune option s'affiche vide et perd la donnee : on injecte donc la
  // valeur courante comme option si elle manque.
  const levelOptions = LEVELS.includes(level) ? LEVELS : [level, ...LEVELS];
  const contractOptions = CONTRACTS.includes(contract)
    ? CONTRACTS
    : [...CONTRACTS, contract];

  const canSearch = titles.length > 0 && locations.length > 0 && !busy;

  function patch(fields: Partial<SearchProfile>) {
    onChange({ ...profile, ...fields });
  }

  const searchLabel = busy
    ? "Recherche et évaluation en cours…"
    : hasResults
      ? "Relancer la recherche"
      : "Lancer la recherche";

  return (
    <div className="card profile-form">
      <h2 className="card-title">Ajustez votre recherche</h2>
      <p className="card-subtitle">
        Déduit de votre CV. Modifiez librement, puis (re)lancez la recherche.
      </p>

      <TagField
        label="Postes recherchés"
        placeholder="Ajouter un intitulé…"
        values={titles}
        onChange={(v) => patch({ titles: v })}
      />
      <TagField
        label="Localisations"
        placeholder="Ajouter une ville ou région…"
        values={locations}
        onChange={(v) => patch({ locations: v })}
      />

      <div className="field-row">
        <label className="field">
          <span className="field-label">Niveau</span>
          <select value={level} onChange={(e) => patch({ level: e.target.value })}>
            {levelOptions.map((l) => (
              <option key={l} value={l}>
                {l || "non précisé"}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Contrat</span>
          <select
            value={contract}
            onChange={(e) => patch({ contract_type: e.target.value })}
          >
            {contractOptions.map((c) => (
              <option key={c} value={c}>
                {c || "indifférent"}
              </option>
            ))}
          </select>
        </label>
      </div>

      <button className="btn-primary" disabled={!canSearch} onClick={onSearch}>
        {searchLabel}
      </button>
    </div>
  );
}

interface TagFieldProps {
  label: string;
  placeholder: string;
  values: string[];
  onChange: (values: string[]) => void;
}

function TagField({ label, placeholder, values, onChange }: TagFieldProps) {
  const [draft, setDraft] = useState("");

  function add() {
    const value = draft.trim();
    if (value && !values.includes(value)) onChange([...values, value]);
    setDraft("");
  }

  return (
    <div className="field">
      <span className="field-label">{label}</span>
      <div className="tags">
        {values.map((value) => (
          <span key={value} className="tag">
            {value}
            <button
              type="button"
              className="tag-remove"
              aria-label={`Retirer ${value}`}
              onClick={() => onChange(values.filter((v) => v !== value))}
            >
              x
            </button>
          </span>
        ))}
      </div>
      <div className="tag-input">
        <input
          value={draft}
          placeholder={placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              add();
            }
          }}
        />
        <button type="button" className="btn-secondary" onClick={add}>
          Ajouter
        </button>
      </div>
    </div>
  );
}

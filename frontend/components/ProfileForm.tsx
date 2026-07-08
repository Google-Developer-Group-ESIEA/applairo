// components/ProfileForm.tsx
// Etape 4 : l'utilisateur ajuste le profil deduit du CV avant de lancer la
// recherche (ajoute/retire des intitules et des localisations, change le niveau
// et le contrat). Etat local, remonte via onSearch au clic sur "Lancer".

"use client";

import { useState } from "react";

import type { SearchProfile } from "@/lib/types";

const LEVELS = ["junior", "intermédiaire", "senior"];
const CONTRACTS = ["", "CDI", "CDD", "stage", "alternance"];

interface Props {
  initial: SearchProfile;
  busy: boolean;
  onSearch: (profile: SearchProfile) => void;
}

export default function ProfileForm({ initial, busy, onSearch }: Props) {
  const [titles, setTitles] = useState<string[]>(initial.titles);
  const [locations, setLocations] = useState<string[]>(initial.locations);
  const [level, setLevel] = useState(initial.level || "intermédiaire");
  const [contract, setContract] = useState(initial.contract_type);

  const canSearch = titles.length > 0 && locations.length > 0 && !busy;

  function submit() {
    onSearch({
      titles,
      locations,
      level,
      contract_type: contract,
    });
  }

  return (
    <div className="card profile-form">
      <h2 className="card-title">Ajustez votre recherche</h2>
      <p className="card-subtitle">
        Deduit de votre CV. Modifiez librement avant de lancer.
      </p>

      <TagField
        label="Postes recherches"
        placeholder="Ajouter un intitule..."
        values={titles}
        onChange={setTitles}
      />
      <TagField
        label="Localisations"
        placeholder="Ajouter une ville ou region..."
        values={locations}
        onChange={setLocations}
      />

      <div className="field-row">
        <label className="field">
          <span className="field-label">Niveau</span>
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Contrat</span>
          <select value={contract} onChange={(e) => setContract(e.target.value)}>
            {CONTRACTS.map((c) => (
              <option key={c} value={c}>
                {c || "indifferent"}
              </option>
            ))}
          </select>
        </label>
      </div>

      <button className="btn-primary" disabled={!canSearch} onClick={submit}>
        {busy ? "Recherche et evaluation en cours..." : "Lancer la recherche"}
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

// components/Uploader.tsx
// Etape 1 : depot du CV (glisser-deposer ou clic). Purement presentationnel :
// il remonte le fichier choisi via onSelect, la logique reseau vit dans SearchFlow.

"use client";

import { useRef, useState } from "react";

const ACCEPT = ".pdf,.docx,.txt,.md";

// Étapes affichées pendant l'analyse (défilées sur une durée fixe côté parent).
const LOAD_PHASES = [
  "Téléchargement du CV",
  "Extraction des informations",
  "Analyse du profil",
];

interface Props {
  onSelect: (file: File) => void;
  busy: boolean;
  currentName?: string | null;
  phase?: number;
}

export default function Uploader({
  onSelect,
  busy,
  currentName,
  phase = 0,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function pick(files: FileList | null) {
    if (files && files.length > 0) onSelect(files[0]);
  }

  return (
    <div className="upload-stage">
      {currentName && !busy && (
        <p className="upload-current">
          CV actuel : <strong>{currentName}</strong>. Déposez-en un autre pour le
          remplacer.
        </p>
      )}
      <div
        className={`uploader${dragging ? " uploader-drag" : ""}${busy ? " uploader-busy" : ""}`}
        onClick={() => !busy && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!busy) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!busy) pick(e.dataTransfer.files);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          hidden
          onChange={(e) => pick(e.target.files)}
        />
        {busy ? (
          <div className="cv-loading">
            <p className="uploader-title">Analyse du CV en cours…</p>
            <ul className="cv-steps">
              {LOAD_PHASES.map((label, i) => {
                const state =
                  i < phase ? "done" : i === phase ? "active" : "pending";
                return (
                  <li key={label} className={`cv-step cv-step-${state}`}>
                    <span className="cv-step-marker" aria-hidden />
                    <span className="cv-step-label">{label}</span>
                    {state === "active" && (
                      <span className="agent-thinking" aria-hidden>
                        <i />
                        <i />
                        <i />
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ) : (
          <>
            <p className="uploader-title">
              {currentName ? "Déposez un nouveau CV" : "Déposez votre CV ici"}
            </p>
            <p className="uploader-hint">ou cliquez pour choisir un fichier</p>
            <p className="uploader-formats">PDF, Word (.docx) ou texte, 5 Mo max</p>
          </>
        )}
      </div>
    </div>
  );
}

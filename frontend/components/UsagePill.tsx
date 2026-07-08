// components/UsagePill.tsx
// Pastille flottante (coin bas-droite) qui affiche la consommation du cycle en
// direct : tokens + coût USD. Montée au niveau de SearchFlow (hors des onglets),
// elle reste visible sur CV / Recherche / Résultats. Le total se met à jour au
// fil de l'eau (profil, puis chaque membre du comité).
//
// État compact = « N tokens · $X » ; au survol, la pastille grandit vers le haut
// et détaille chaque appel + le total.

"use client";

import type { ProgressState } from "@/lib/progress";
import type { Usage } from "@/lib/types";

const fmtTokens = (n: number) => n.toLocaleString("fr-FR");
const fmtUsd = (n: number) => `$${n.toFixed(4)}`;

export default function UsagePill({
  profileUsage,
  progress,
}: {
  profileUsage: Usage | null;
  progress: ProgressState | null;
}) {
  const members = progress?.members ?? [];
  const memberUsage = progress?.memberUsage ?? {};

  // Un appel = une ligne, dans l'ordre du cycle : profil puis membres revenus.
  const rows: { label: string; usage: Usage }[] = [
    ...(profileUsage ? [{ label: "Extraction du profil", usage: profileUsage }] : []),
    ...members.filter((m) => m in memberUsage).map((m) => ({ label: m, usage: memberUsage[m] })),
  ];
  if (rows.length === 0) return null;

  const totalTokens = rows.reduce((s, r) => s + r.usage.total_tokens, 0);
  const totalCost = rows.reduce((s, r) => s + r.usage.cost_usd, 0);
  const model = rows[0].usage.model;

  return (
    <div className="usage-pill" role="status" aria-label="Consommation en tokens et coût" tabIndex={0}>
      {/* Détail (au-dessus du compact) : révélé au survol, grandit vers le haut. */}
      <div className="usage-pill-detail">
        <p className="usage-pill-head">
          Consommation<span>tokens réels · tarifs Gemini</span>
        </p>
        <div className="usage-rows">
          {rows.map((r) => (
            <div key={r.label} className="usage-row">
              <span className="usage-label">{r.label}</span>
              <span className="usage-tokens">{fmtTokens(r.usage.total_tokens)} tokens</span>
              <span className="usage-cost">~{fmtUsd(r.usage.cost_usd)}</span>
            </div>
          ))}
          <div className="usage-row usage-row-total">
            <span className="usage-label">Total ({rows.length} appels)</span>
            <span className="usage-tokens">{fmtTokens(totalTokens)} tokens</span>
            <span className="usage-cost">~{fmtUsd(totalCost)}</span>
          </div>
        </div>
        {model && <p className="usage-foot">{model}</p>}
      </div>

      {/* Compact (toujours visible), ancré en bas de la pastille. */}
      <div className="usage-pill-compact">
        <span className="usage-pill-dot" aria-hidden />
        {fmtTokens(totalTokens)} tokens · {fmtUsd(totalCost)}
      </div>
    </div>
  );
}

// app/comment-ca-marche/page.tsx
// Page explicative « Comment ça marche » : décrit le VRAI pipeline agentique
// (l'entonnoir qui maîtrise le coût LLM), pas l'habillage visuel de l'app.
//
// Ce fichier reste un composant SERVEUR (il exporte `metadata`). Tout l'affichage
// anime au defilement vit dans le composant client `HowItWorks`.

import HowItWorks from "./HowItWorks";

export const metadata = {
  title: "Comment ça marche - Applairo",
  description:
    "Le pipeline agentique d'Applairo, étape par étape : de votre CV aux offres notées par un comité d'agents.",
};

export default function Page() {
  return <HowItWorks />;
}

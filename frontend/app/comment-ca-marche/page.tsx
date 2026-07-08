// app/comment-ca-marche/page.tsx
// Page explicative « Comment ça marche » : décrit le VRAI pipeline agentique
// (l'entonnoir qui maîtrise le coût LLM), pas l'habillage visuel de l'app.
//
// Composant serveur statique (aucune interactivité) : pas de "use client".
// Le contenu suit le fil du backend : CV -> profil -> recherche -> sélection ->
// comité, en distinguant à chaque étape ce qui coûte un appel IA de ce qui n'en
// coûte pas. Les chiffres cités sont les valeurs PAR DÉFAUT (config.py) : ils
// sont pilotés par la configuration, pas figés dans le code.

import Link from "next/link";

export const metadata = {
  title: "Comment ça marche - Applairo",
  description:
    "Le pipeline agentique d'Applairo, étape par étape : de votre CV aux offres notées par un comité d'agents.",
};

type Cost = "ia" | "mecanique";

const STEPS: {
  n: number;
  title: string;
  cost: Cost;
  costLabel: string;
  body: string;
  detail?: string;
}[] = [
  {
    n: 1,
    title: "Lecture du CV",
    cost: "mecanique",
    costLabel: "Sans IA",
    body:
      "Votre fichier (PDF, DOCX ou TXT) est lu en mémoire pour en extraire le texte brut. Étape purement mécanique, sans modèle de langage.",
    detail:
      "Le CV est une donnée personnelle : il n'est jamais écrit sur le disque. On ne travaille que sur les octets reçus.",
  },
  {
    n: 2,
    title: "Déduction du profil",
    cost: "ia",
    costLabel: "1 appel IA",
    body:
      "Un premier agent (Gemini) lit le texte du CV et en déduit un profil de recherche structuré : intitulés de poste, localisations, niveau et type de contrat.",
    detail:
      "La sortie est contrainte à un schéma JSON : pas de texte libre à re-parser. L'agent traduit les compétences en intitulés que les recruteurs emploient réellement, et ajoute au besoin une variante enrichie (alternance, stage).",
  },
  {
    n: 3,
    title: "Recherche multi-requêtes",
    cost: "mecanique",
    costLabel: "Sans IA",
    body:
      "Le profil est éclaté en requêtes (chaque intitulé croisé avec chaque localisation), envoyées en parallèle à l'API d'offres d'emploi Adzuna.",
    detail:
      "Le nombre de combinaisons est plafonné (10 par défaut). Les requêtes partent simultanément ; une requête en échec est isolée et ne casse pas les autres.",
  },
  {
    n: 4,
    title: "Sélection des meilleures",
    cost: "mecanique",
    costLabel: "Sans IA",
    body:
      "Les résultats des requêtes sont entrelacés en round-robin, dédoublonnés par URL, puis coupés aux meilleures offres avant l'étape coûteuse.",
    detail:
      "L'entrelacement garantit que chaque requête contribue équitablement, plutôt que la première ne sature la liste. On ne garde que le haut du panier (12 par défaut) pour borner le coût de l'étape suivante.",
  },
  {
    n: 5,
    title: "Le comité délibère",
    cost: "ia",
    costLabel: "3 appels IA",
    body:
      "Trois agents aux points de vue distincts notent les offres retenues, chacun en un seul appel groupé. Leurs notes sont moyennées en une note globale, et les offres sont classées.",
    detail:
      "C'est ici que vit le vrai temps de calcul : les trois agents délibèrent réellement, en parallèle. Chaque membre est notifié dès qu'il termine, sans attendre les autres.",
  },
];

const MEMBERS: { initials: string; name: string; lens: string }[] = [
  {
    initials: "RH",
    name: "RH",
    lens:
      "Adéquation humaine : culture d'entreprise, ton et mots-clés de l'annonce en regard du profil, cohérence du parcours.",
  },
  {
    initials: "TL",
    name: "Tech lead",
    lens:
      "Crédibilité technique : les compétences et l'expérience du profil face aux exigences techniques de l'offre. Exigeant sur les écarts de stack ou de séniorité.",
  },
  {
    initials: "M",
    name: "Marché",
    lens:
      "Réalisme de l'offre : cohérence salaire / séniorité, attractivité, localisation. Une note haute = offre réaliste et intéressante.",
  },
];

const PRINCIPLES: { title: string; body: string }[] = [
  {
    title: "Un entonnoir qui maîtrise le coût",
    body:
      "Le fan-out et le tri se font sans IA. Seuls la lecture du profil et le comité appellent le modèle, soit 4 appels par recherche, quel que soit le nombre d'offres trouvées.",
  },
  {
    title: "Sans état",
    body:
      "Le backend ne stocke aucune session. Le profil déduit vit côté navigateur : vous pouvez l'ajuster et relancer une recherche sans re-téléverser votre CV.",
  },
  {
    title: "Architecture hexagonale",
    body:
      "Le cœur du pipeline orchestre des ports abstraits, jamais des technologies. Adzuna et Gemini sont des adaptateurs interchangeables, branchés à la périphérie.",
  },
  {
    title: "Résilient et diffusé en direct",
    body:
      "Une requête ou un membre du comité qui échoue n'interrompt pas la recherche. L'avancement est diffusé au fil de l'eau (flux NDJSON) et rendu dans la frise des agents.",
  },
];

export default function HowItWorks() {
  return (
    <main className="flow hiw">
      <header className="flow-header">
        <div className="hiw-back">
          <Link href="/" className="btn-secondary">
            Retour à l&apos;application
          </Link>
        </div>
        <h1 className="brand">Comment ça marche</h1>
        <p className="tagline">
          De votre CV aux offres notées, voici le trajet exact que suit Applairo,
          étape par étape.
        </p>
      </header>

      {/* Le principe clé, mis en avant : le coût LLM est borné par construction. */}
      <section className="hiw-keystone card">
        <p className="hiw-keystone-eyebrow">Le principe</p>
        <p className="hiw-keystone-headline">
          Une recherche complète ne coûte que{" "}
          <strong>4 appels au modèle</strong>, quel que soit le nombre d&apos;offres.
        </p>
        <p className="hiw-keystone-body">
          Tout ce qui peut se faire sans intelligence artificielle (lire le CV,
          interroger les offres, trier) se fait sans elle. Le modèle n&apos;est
          sollicité qu&apos;à deux moments : déduire votre profil (1 appel) et
          faire délibérer le comité (3 appels groupés). Chaque membre note{" "}
          <strong>toutes</strong> les offres en un seul appel : la facture ne
          gonfle pas avec le volume.
        </p>
      </section>

      {/* Le pipeline : rail vertical, une étape par phase réelle du backend. */}
      <section className="hiw-section">
        <h2 className="hiw-h2">Le pipeline, étape par étape</h2>
        <ol className="hiw-steps">
          {STEPS.map((s) => (
            <li key={s.n} className={`hiw-step hiw-step-${s.cost}`}>
              <div className="hiw-rail">
                <span className="hiw-marker">{s.n}</span>
              </div>
              <div className="hiw-step-body">
                <div className="hiw-step-head">
                  <h3 className="hiw-step-title">{s.title}</h3>
                  <span className={`hiw-badge hiw-badge-${s.cost}`}>
                    {s.costLabel}
                  </span>
                </div>
                <p className="hiw-step-text">{s.body}</p>
                {s.detail && <p className="hiw-step-detail">{s.detail}</p>}
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* Le comité : trois points de vue, détaillés. */}
      <section className="hiw-section">
        <h2 className="hiw-h2">Le comité, trois regards</h2>
        <p className="hiw-section-lead">
          Le classement final n&apos;est pas l&apos;avis d&apos;un seul agent,
          mais la synthèse de trois points de vue complémentaires. Ils travaillent
          en parallèle ; leurs notes sont ensuite moyennées.
        </p>
        <div className="hiw-members">
          {MEMBERS.map((m) => (
            <div key={m.name} className="hiw-member card">
              <span className="agent-avatar">{m.initials}</span>
              <div>
                <p className="agent-name">{m.name}</p>
                <p className="hiw-member-lens">{m.lens}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Les partis pris d'architecture. */}
      <section className="hiw-section">
        <h2 className="hiw-h2">Les partis pris</h2>
        <div className="hiw-principles">
          {PRINCIPLES.map((p) => (
            <div key={p.title} className="hiw-principle card">
              <h3 className="hiw-principle-title">{p.title}</h3>
              <p className="hiw-principle-body">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="hiw-footer">
        <Link href="/" className="btn-primary hiw-cta">
          Analyser mon CV
        </Link>
      </footer>
    </main>
  );
}

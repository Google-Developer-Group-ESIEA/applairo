// app/comment-ca-marche/HowItWorks.tsx
// Rendu anime de la page « Comment ça marche ». Composant client : il gere le
// reveal au defilement (IntersectionObserver) et les micro-interactions.
//
// Contraintes d'accessibilite tenues :
//   - tout est visible immediatement si `prefers-reduced-motion: reduce` ;
//   - les animations n'utilisent que `transform` / `opacity` (pas de reflow) ;
//   - entree en ease-out, echelonnee, jamais d'animation infinie decorative
//     (hors decor de fond, lui aussi coupe en reduced-motion).
//
// Le contenu suit le fil du backend : CV -> profil -> recherche -> selection ->
// comite, en distinguant a chaque etape ce qui coute un appel IA. Les chiffres
// cites sont les valeurs PAR DEFAUT (config.py), pilotees par la configuration.

"use client";

import Link from "next/link";
import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

/* --- Icones (trace Lucide, stroke 1.75, currentColor) ------------------- */

type IconProps = { className?: string };

function IconDoc({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M14 3v4a1 1 0 0 0 1 1h4" />
      <path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z" />
      <path d="M9 12h6M9 16h6M9 8h1" />
    </svg>
  );
}
function IconSparkles({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M12 3l1.9 4.6L18.5 9.5 13.9 11.4 12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3Z" />
      <path d="M19 14l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8.8-2Z" />
    </svg>
  );
}
function IconSearch({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}
function IconFunnel({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M3 4h18l-7 8v7l-4 2v-9L3 4Z" />
    </svg>
  );
}
function IconUsers({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13A4 4 0 0 1 16 11" />
    </svg>
  );
}
function IconCoins({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <circle cx="8" cy="8" r="6" />
      <path d="M18.09 10.37A6 6 0 1 1 10.34 18M7 6h1v4M16.71 13.88l.7.71-2.82 2.82" />
    </svg>
  );
}
function IconDatabase({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v6c0 1.66 3.58 3 8 3s8-1.34 8-3V5" />
      <path d="M4 11v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" />
    </svg>
  );
}
function IconHexagon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M12 2.5l8.5 4.9v9.2L12 21.5l-8.5-4.9V7.4L12 2.5Z" />
      <path d="M12 7.5l4 2.3v4.4l-4 2.3-4-2.3V9.8l4-2.3Z" />
    </svg>
  );
}
function IconBroadcast({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <circle cx="12" cy="12" r="2" />
      <path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49M19.07 4.93a10 10 0 0 1 0 14.14M4.93 19.07a10 10 0 0 1 0-14.14" />
    </svg>
  );
}

/* --- Donnees ------------------------------------------------------------ */

type Cost = "ia" | "mecanique";

const STEPS: {
  n: number;
  title: string;
  cost: Cost;
  costLabel: string;
  body: string;
  detail: string;
  Icon: (p: IconProps) => ReactNode;
}[] = [
  {
    n: 1,
    title: "Lecture du CV",
    cost: "mecanique",
    costLabel: "Sans IA",
    Icon: IconDoc,
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
    Icon: IconSparkles,
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
    Icon: IconSearch,
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
    Icon: IconFunnel,
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
    Icon: IconUsers,
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

const PRINCIPLES: {
  title: string;
  body: string;
  Icon: (p: IconProps) => ReactNode;
}[] = [
  {
    title: "Un entonnoir qui maîtrise le coût",
    Icon: IconCoins,
    body:
      "Le fan-out et le tri se font sans IA. Seuls la lecture du profil et le comité appellent le modèle, soit 4 appels par recherche, quel que soit le nombre d'offres trouvées.",
  },
  {
    title: "Sans état",
    Icon: IconDatabase,
    body:
      "Le backend ne stocke aucune session. Le profil déduit vit côté navigateur : vous pouvez l'ajuster et relancer une recherche sans re-téléverser votre CV.",
  },
  {
    title: "Architecture hexagonale",
    Icon: IconHexagon,
    body:
      "Le cœur du pipeline orchestre des ports abstraits, jamais des technologies. Adzuna et Gemini sont des adaptateurs interchangeables, branchés à la périphérie.",
  },
  {
    title: "Résilient et diffusé en direct",
    Icon: IconBroadcast,
    body:
      "Une requête ou un membre du comité qui échoue n'interrompt pas la recherche. L'avancement est diffusé au fil de l'eau (flux NDJSON) et rendu dans la frise des agents.",
  },
];

/* --- Reveal au defilement ----------------------------------------------- */

// Enveloppe un bloc et le revele quand il entre dans le viewport. Coupe net
// (visible d'emblee) si l'utilisateur demande moins d'animation.
function Reveal({
  children,
  className = "",
  delay = 0,
  tag = "div",
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  tag?: "div" | "li" | "section" | "header";
}) {
  const ref = useRef<HTMLElement | null>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      setShown(true);
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShown(true);
          io.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const Tag = tag as "div";
  return (
    <Tag
      ref={ref as React.RefObject<HTMLDivElement>}
      className={`reveal${shown ? " reveal-in" : ""} ${className}`.trim()}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </Tag>
  );
}

/* --- Page --------------------------------------------------------------- */

export default function HowItWorks() {
  return (
    <main className="flow hiw">
      {/* Decor de fond : deux halos qui derivent lentement (coupes en
          reduced-motion). Purement decoratif, donc masque aux lecteurs. */}
      <div className="hiw-aurora" aria-hidden>
        <span className="hiw-orb hiw-orb-1" />
        <span className="hiw-orb hiw-orb-2" />
      </div>

      <Link href="/" className="btn-secondary hiw-corner">
        Retour à l&apos;application
      </Link>

      <Reveal tag="header" className="flow-header hiw-hero">
        <span className="hiw-eyebrow">Pipeline agentique</span>
        <h1 className="brand hiw-title">Comment ça marche</h1>
        <p className="tagline">
          De votre CV aux offres notées, voici le trajet exact que suit Applairo,
          étape par étape.
        </p>
      </Reveal>

      {/* Le principe cle : le cout LLM est borne par construction. */}
      <Reveal tag="section" className="hiw-keystone card">
        <p className="hiw-keystone-eyebrow">Le principe</p>
        <div className="hiw-formula">
          <span className="hiw-chip hiw-chip-ia">
            <strong>1</strong>
            <span>profil</span>
          </span>
          <span className="hiw-op">+</span>
          <span className="hiw-chip hiw-chip-ia">
            <strong>3</strong>
            <span>comité</span>
          </span>
          <span className="hiw-op">=</span>
          <span className="hiw-chip hiw-chip-total">
            <strong>4</strong>
            <span>appels IA</span>
          </span>
        </div>
        <p className="hiw-keystone-headline">
          Une recherche complète ne coûte que{" "}
          <strong>4 appels au modèle</strong>, quel que soit le nombre
          d&apos;offres.
        </p>
        <p className="hiw-keystone-body">
          Tout ce qui peut se faire sans intelligence artificielle (lire le CV,
          interroger les offres, trier) se fait sans elle. Chaque membre du comité
          note <strong>toutes</strong> les offres en un seul appel groupé : la
          facture ne gonfle pas avec le volume.
        </p>
      </Reveal>

      {/* Le pipeline : rail vertical, une etape par phase reelle du backend. */}
      <section className="hiw-section">
        <Reveal tag="header" className="hiw-section-head">
          <h2 className="hiw-h2">Le pipeline, étape par étape</h2>
        </Reveal>
        <ol className="hiw-steps">
          {STEPS.map((s, i) => (
            <Reveal
              key={s.n}
              tag="li"
              delay={i * 90}
              className={`hiw-step hiw-step-${s.cost}`}
            >
              <div className="hiw-rail">
                <span className="hiw-marker">
                  <s.Icon className="hiw-marker-icon" />
                  <span className="hiw-marker-n">{s.n}</span>
                </span>
              </div>
              <div className="hiw-step-body">
                <div className="hiw-step-head">
                  <h3 className="hiw-step-title">{s.title}</h3>
                  <span className={`hiw-badge hiw-badge-${s.cost}`}>
                    {s.cost === "ia" && (
                      <IconSparkles className="hiw-badge-icon" />
                    )}
                    {s.costLabel}
                  </span>
                </div>
                <p className="hiw-step-text">{s.body}</p>
                <p className="hiw-step-detail">{s.detail}</p>
              </div>
            </Reveal>
          ))}
        </ol>
      </section>

      {/* Le comite : trois points de vue, detailles. */}
      <section className="hiw-section">
        <Reveal tag="header" className="hiw-section-head">
          <h2 className="hiw-h2">Le comité, trois regards</h2>
          <p className="hiw-section-lead">
            Le classement final n&apos;est pas l&apos;avis d&apos;un seul agent,
            mais la synthèse de trois points de vue complémentaires. Ils
            travaillent en parallèle ; leurs notes sont ensuite moyennées.
          </p>
        </Reveal>
        <div className="hiw-members">
          {MEMBERS.map((m, i) => (
            <Reveal key={m.name} delay={i * 90} className="hiw-member card">
              <span className="agent-avatar hiw-member-avatar">
                {m.initials}
              </span>
              <div>
                <p className="agent-name">{m.name}</p>
                <p className="hiw-member-lens">{m.lens}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Les partis pris d'architecture. */}
      <section className="hiw-section">
        <Reveal tag="header" className="hiw-section-head">
          <h2 className="hiw-h2">Les partis pris</h2>
        </Reveal>
        <div className="hiw-principles">
          {PRINCIPLES.map((p, i) => (
            <Reveal key={p.title} delay={i * 80} className="hiw-principle card">
              <span className="hiw-principle-icon">
                <p.Icon />
              </span>
              <h3 className="hiw-principle-title">{p.title}</h3>
              <p className="hiw-principle-body">{p.body}</p>
            </Reveal>
          ))}
        </div>
      </section>

      <Reveal className="hiw-footer">
        <Link href="/" className="btn-primary hiw-cta">
          Analyser mon CV
        </Link>
      </Reveal>
    </main>
  );
}

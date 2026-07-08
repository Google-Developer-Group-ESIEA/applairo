// app/comment-ca-marche/HowItWorks.tsx
// Rendu anime de la page « Comment ça marche », ecrite pour l'utilisateur final
// (un candidat qui veut booster sa recherche avec des agents IA), pas pour un
// developpeur : on parle benefice et confiance, jamais tuyauterie technique.
//
// Composant client : il gere le reveal au defilement (IntersectionObserver) et
// les micro-interactions. Accessibilite tenue :
//   - tout est visible d'emblee si `prefers-reduced-motion: reduce` ;
//   - les animations n'utilisent que `transform` / `opacity` (pas de reflow).

"use client";

import Link from "next/link";
import {
  Briefcase,
  Code2,
  FileText,
  Filter,
  Handshake,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Star,
  TrendingUp,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";

/* --- Donnees (icones : bibliotheque Lucide) ----------------------------- */

type Cost = "ia" | "auto";

const STEPS: {
  n: number;
  title: string;
  cost: Cost;
  body: string;
  Icon: LucideIcon;
}[] = [
  {
    n: 1,
    title: "On lit votre CV",
    cost: "auto",
    Icon: FileText,
    body: "Vous déposez votre CV (PDF, Word ou texte) et on en extrait vos compétences et votre parcours. Rien n'est conservé.",
  },
  {
    n: 2,
    title: "L'IA cerne votre profil",
    cost: "ia",
    Icon: Sparkles,
    body: "Un agent identifie les postes, les lieux et le niveau qui vous correspondent, même si votre CV emploie des termes peu courants.",
  },
  {
    n: 3,
    title: "On ratisse les offres",
    cost: "auto",
    Icon: Search,
    body: "Plusieurs recherches partent en parallèle sur de vraies annonces, pour couvrir tous les postes et toutes les villes qui vous vont.",
  },
  {
    n: 4,
    title: "On garde le meilleur",
    cost: "auto",
    Icon: Filter,
    body: "Les doublons sont écartés et seules les offres les plus prometteuses passent devant le comité.",
  },
  {
    n: 5,
    title: "Trois experts notent chaque offre",
    cost: "ia",
    Icon: Users,
    body: "Le comité évalue les offres retenues selon trois regards, puis les classe des plus adaptées aux moins.",
  },
];

const MEMBERS: {
  key: string;
  name: string;
  role: string;
  lens: string;
  Icon: LucideIcon;
}[] = [
  {
    key: "rh",
    name: "RH",
    role: "Le facteur humain",
    lens: "Culture d'entreprise, ton de l'annonce et cohérence de votre parcours.",
    Icon: Handshake,
  },
  {
    key: "tech",
    name: "Tech lead",
    role: "La crédibilité technique",
    lens: "Vos compétences face aux exigences du poste, sans complaisance sur les écarts.",
    Icon: Code2,
  },
  {
    key: "market",
    name: "Marché",
    role: "Le réalisme",
    lens: "Salaire, séniorité, attractivité : l'offre est-elle sérieuse et faite pour vous ?",
    Icon: TrendingUp,
  },
];

const PRINCIPLES: {
  key: string;
  title: string;
  body: string;
  Icon: LucideIcon;
}[] = [
  {
    key: "rh",
    title: "Votre CV reste privé",
    body: "Il est lu en mémoire le temps de l'analyse, jamais enregistré sur nos serveurs.",
    Icon: ShieldCheck,
  },
  {
    key: "tech",
    title: "De vraies offres, à jour",
    body: "Les postes proviennent d'annonces d'emploi réelles, pas d'une base figée.",
    Icon: Briefcase,
  },
  {
    key: "market",
    title: "Une note toujours expliquée",
    body: "Chaque offre affiche sa note et l'avis du comité : vous savez pourquoi elle vous est proposée.",
    Icon: Star,
  },
  {
    key: "rh",
    title: "Vous gardez la main",
    body: "Ajustez les postes ou les villes et relancez la recherche, sans re-téléverser votre CV.",
    Icon: SlidersHorizontal,
  },
];

/* --- Reveal au defilement ----------------------------------------------- */

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
      <div className="hiw-aurora" aria-hidden>
        <span className="hiw-orb hiw-orb-1" />
        <span className="hiw-orb hiw-orb-2" />
      </div>

      <Link href="/" className="btn-secondary hiw-corner">
        Retour à l&apos;application
      </Link>

      <Reveal tag="header" className="flow-header hiw-hero">
        <h1 className="brand hiw-title">Comment ça marche</h1>
        <p className="tagline">
          Confiez votre CV à une équipe d&apos;agents IA. Ils cherchent, trient et
          notent les offres à votre place, pour ne garder que celles faites pour
          vous.
        </p>
      </Reveal>

      {/* La promesse : ce n'est pas un algorithme opaque, c'est un comite. */}
      <Reveal tag="section" className="hiw-keystone card">
        <div className="hiw-verdict">
          <span className="hiw-vchip hiw-vchip-rh">RH</span>
          <span className="hiw-vchip hiw-vchip-tech">Tech lead</span>
          <span className="hiw-vchip hiw-vchip-market">Marché</span>
          <span className="hiw-varrow" aria-hidden />
          <span className="hiw-vscore">
            92<small>/100</small>
          </span>
        </div>
        <p className="hiw-keystone-headline">
          Chaque offre est notée par <strong>trois experts IA</strong>, pas par un
          algorithme opaque.
        </p>
        <p className="hiw-keystone-body">
          Vous ne recevez pas une liste filtrée à l&apos;aveugle. Trois agents aux
          regards complémentaires jugent chaque poste, le classent, et vous disent
          pourquoi il vous correspond.
        </p>
      </Reveal>

      {/* Le parcours, etape par etape. */}
      <section className="hiw-section">
        <Reveal tag="header" className="hiw-section-head">
          <h2 className="hiw-h2">Le parcours, étape par étape</h2>
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
                  {s.cost === "ia" && (
                    <span className="hiw-badge hiw-badge-ia">
                      <Sparkles className="hiw-badge-icon" />
                      IA
                    </span>
                  )}
                </div>
                <p className="hiw-step-text">{s.body}</p>
              </div>
            </Reveal>
          ))}
        </ol>
      </section>

      {/* Le comite : trois cartes-personnages, chacune sa couleur. */}
      <section className="hiw-section">
        <Reveal tag="header" className="hiw-section-head">
          <h2 className="hiw-h2">Rencontrez le comité</h2>
          <p className="hiw-section-lead">
            Trois agents, trois regards complémentaires. Ils notent chaque offre en
            parallèle, puis on fait la moyenne pour votre classement.
          </p>
        </Reveal>
        <div className="hiw-members">
          {MEMBERS.map((m, i) => (
            <Reveal
              key={m.name}
              delay={i * 90}
              className={`hiw-member hiw-member-${m.key} card`}
            >
              <span className="hiw-member-avatar">
                <m.Icon />
              </span>
              <p className="hiw-member-name">{m.name}</p>
              <p className="hiw-member-role">{m.role}</p>
              <p className="hiw-member-lens">{m.lens}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Ce qui compte pour vous : reassurances utilisateur. */}
      <section className="hiw-section">
        <Reveal tag="header" className="hiw-section-head">
          <h2 className="hiw-h2">Pourquoi lui faire confiance</h2>
        </Reveal>
        <div className="hiw-principles">
          {PRINCIPLES.map((p, i) => (
            <Reveal
              key={p.title}
              delay={i * 80}
              className={`hiw-principle hiw-principle-${p.key} card`}
            >
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

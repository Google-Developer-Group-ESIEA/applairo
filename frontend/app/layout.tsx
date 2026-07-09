// app/layout.tsx
// Layout racine de l'application Next.js.

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ApplaiNow - GDG ESIEA",
  description:
    "L'agent IA qui transforme votre profil en offres d'emploi ciblées.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}

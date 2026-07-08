// lib/profile.ts
// Extraction du profil à partir de l'historique de conversation.
//
// Logique de PRÉSENTATION pure (aucun appel réseau), volontairement gardée côté
// frontend : le backend n'a pas à connaître ce panneau pédagogique.
//
// L'agent pose les 4 questions dans un ordre fixe : la Nième réponse de
// l'utilisateur correspond donc à la Nième étape du profil (hypothèse d'ordre
// strict, héritée de la V0).

import type { ChatMessage } from "./types";

export interface ProfileStep {
  key: string;
  label: string;
}

export const PROFILE_STEPS: ProfileStep[] = [
  { key: "title", label: "Poste recherché" },
  { key: "location", label: "Localisation" },
  { key: "experience", label: "Niveau d'expérience" },
  { key: "contract_type", label: "Type de contrat" },
];

export type Profile = Record<string, string | null>;

export function extractProfile(messages: ChatMessage[]): Profile {
  const profile: Profile = Object.fromEntries(
    PROFILE_STEPS.map((step) => [step.key, null]),
  );

  const userMessages = messages
    .filter((m) => m.role === "user")
    .map((m) => m.content);

  PROFILE_STEPS.forEach((step, index) => {
    if (index < userMessages.length) {
      profile[step.key] = userMessages[index];
    }
  });

  return profile;
}

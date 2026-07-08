// lib/backend.ts
// Accès serveur au backend (BFF). Utilisé UNIQUEMENT par les route handlers
// (app/api/**), jamais par le navigateur : l'URL du backend reste privée et le
// front n'a aucun souci de CORS.
//
// En Docker, BACKEND_URL vaut http://backend:8000 (nom du service compose).
//
// Le Content-Type n'est PAS forcé ici : les appels JSON le posent eux-mêmes, et
// l'upload de CV (multipart) laisse fetch calculer sa propre frontière (boundary).

export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function backendFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, { ...init, cache: "no-store" });
}

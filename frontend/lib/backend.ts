// lib/backend.ts
// Accès serveur au backend (BFF). Utilisé UNIQUEMENT par les route handlers
// (app/api/**), jamais par le navigateur : l'URL du backend reste privée et le
// front n'a aucun souci de CORS.
//
// En Docker, BACKEND_URL vaut http://backend:8000 (nom du service compose).

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function backendFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
}

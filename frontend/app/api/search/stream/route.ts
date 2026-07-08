// app/api/search/stream/route.ts
// Proxy serveur du flux de recherche. Contrairement aux autres proxys, il ne
// bufferise PAS : il relaie le ReadableStream du backend tel quel, sinon
// l'affichage temps réel arriverait d'un bloc à la fin.
//
// force-dynamic + passage direct de `upstream.body` = streaming de bout en bout.

import { NextRequest } from "next/server";

import { backendFetch } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const body = await req.text();
  const upstream = await backendFetch("/api/search/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  // En cas d'erreur (ex: 400 profil vide), le backend renvoie un JSON classique,
  // pas un flux : on le relaie tel quel, le client lira le `detail`.
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type":
        upstream.headers.get("Content-Type") ?? "application/x-ndjson",
      "Cache-Control": "no-cache",
    },
  });
}

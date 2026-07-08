// app/api/search/route.ts
// Proxy serveur : relaie une recherche (profil edite) vers le backend.

import { NextRequest, NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await backendFetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

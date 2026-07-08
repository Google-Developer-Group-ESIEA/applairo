// app/api/sessions/route.ts
// Proxy serveur : ouvre une session côté backend.

import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST() {
  const res = await backendFetch("/api/sessions", { method: "POST" });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

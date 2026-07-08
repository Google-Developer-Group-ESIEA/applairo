// app/api/chat/route.ts
// Proxy serveur : transmet un message utilisateur au backend.

import { NextRequest, NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await backendFetch("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

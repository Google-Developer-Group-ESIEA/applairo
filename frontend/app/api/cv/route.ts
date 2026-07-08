// app/api/cv/route.ts
// Proxy serveur : relaie l'upload du CV (multipart) vers le backend.
//
// On reconstruit un FormData et on le passe à fetch : celui-ci pose lui-meme
// l'en-tete multipart avec la bonne frontiere (boundary). Le fichier ne touche
// jamais le disque cote frontend.

import { NextRequest, NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST(req: NextRequest) {
  const incoming = await req.formData();
  const res = await backendFetch("/api/cv", { method: "POST", body: incoming });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

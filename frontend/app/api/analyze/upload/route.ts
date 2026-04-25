import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const res = await fetch(`${BACKEND}/api/analyze/upload`, {
    method: "POST",
    body: form,
    cache: "no-store",
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

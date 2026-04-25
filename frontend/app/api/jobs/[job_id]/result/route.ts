import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET(
  _req: NextRequest,
  { params }: { params: { job_id: string } }
) {
  const res = await fetch(`${BACKEND}/api/jobs/${params.job_id}/result`, {
    cache: "no-store",
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return proxyRequest(request, resolvedParams.path, "GET");
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return proxyRequest(request, resolvedParams.path, "POST");
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return proxyRequest(request, resolvedParams.path, "PATCH");
}

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  const path = pathSegments.join("/");
  // Backend routes: demo routes go to /demo/, others go to /spans/
  let backendPath: string;
  if (path.startsWith("demo/")) {
    backendPath = path; // demo routes stay as-is
  } else if (path.startsWith("spans/")) {
    backendPath = path; // already has spans prefix
  } else {
    backendPath = `spans/${path}`; // other routes get spans prefix
  }
  const url = new URL(backendPath, API_BASE_URL);
  
  // Forward query parameters
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value);
  });

  // Get tenant ID from header (or use default)
  const tenantId = request.headers.get("x-tenant-id") || "default";

  // Prepare fetch options
  const options: RequestInit = {
    method,
    headers: {
      "x-tenant-id": tenantId,
      "Content-Type": "application/json",
    },
  };

  // Include body for POST requests
  if (method === "POST") {
    try {
      const body = await request.text();
      if (body) {
        options.body = body;
      }
    } catch (e) {
      // No body
    }
  }

  try {
    const response = await fetch(url.toString(), options);
    const data = await response.json();
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: "Proxy error", message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}


import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const COLLECTOR_URL = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";

// Log on module load
console.log("[API Route] Module loaded, COLLECTOR_URL:", COLLECTOR_URL);

export async function POST(request: NextRequest) {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    
    console.log("[API Route] Auth check - token exists:", !!token);
    
    if (!token) {
      console.error("[API Route] No auth token found");
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    let body;
    try {
      body = await request.json();
      console.log("[API Route] Request body parsed:", body);
    } catch (e) {
      console.error("[API Route] Failed to parse request body:", e);
      return NextResponse.json(
        { error: "Invalid request body" },
        { status: 400 }
      );
    }

    const { name } = body;

    if (!name || !name.trim()) {
      return NextResponse.json(
        { error: "Name is required" },
        { status: 400 }
      );
    }

    const url = `${COLLECTOR_URL}/clerk/api-keys`;
    const requestBody = { name: name.trim() };
    
    console.log(`[API Route] Creating API key for user`);
    console.log(`[API Route] Collector URL: ${COLLECTOR_URL}`);
    console.log(`[API Route] Full URL: ${url}`);
    console.log(`[API Route] Request body:`, requestBody);
    console.log(`[API Route] Token length: ${token.length}`);
    
    let response: Response;
    try {
      response = await fetch(url, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });
    } catch (fetchError) {
      console.error("[API Route] Fetch error details:", {
        error: fetchError,
        message: fetchError instanceof Error ? fetchError.message : String(fetchError),
        stack: fetchError instanceof Error ? fetchError.stack : undefined,
        url: url,
        collectorUrl: COLLECTOR_URL
      });
      return NextResponse.json(
        { 
          error: `Failed to connect to collector at ${COLLECTOR_URL}: ${fetchError instanceof Error ? fetchError.message : "Unknown error"}. Make sure the collector is running.` 
        },
        { status: 500 }
      );
    }

    console.log(`[API Route] Response status: ${response.status}, ok: ${response.ok}`);

    if (!response.ok) {
      let errorText: string;
      try {
        errorText = await response.text();
        // Try to parse as JSON
        try {
          const errorJson = JSON.parse(errorText);
          console.error("[API Route] Collector API error (JSON):", response.status, errorJson);
          return NextResponse.json(
            { error: errorJson.detail || errorJson.error || errorText },
            { status: response.status }
          );
        } catch {
          // Not JSON, use as text
          console.error("[API Route] Collector API error (text):", response.status, errorText);
          return NextResponse.json(
            { error: errorText || `Collector API error: ${response.status}` },
            { status: response.status }
          );
        }
      } catch (e) {
        console.error("[API Route] Failed to read error response:", e);
        return NextResponse.json(
          { error: `Collector API error: ${response.status}` },
          { status: response.status }
        );
      }
    }

    let data;
    try {
      data = await response.json();
      console.log("[API Route] Success, returning data:", { ...data, key: data.key ? `${data.key.substring(0, 10)}...` : "NO KEY" });
    } catch (jsonError) {
      console.error("[API Route] Failed to parse response as JSON:", jsonError);
      const text = await response.text();
      console.error("[API Route] Response text:", text);
      return NextResponse.json(
        { error: `Invalid JSON response from collector: ${text.substring(0, 200)}` },
        { status: 500 }
      );
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error("[API Route] Top-level error:", error);
    console.error("[API Route] Error type:", error instanceof Error ? error.constructor.name : typeof error);
    console.error("[API Route] Error message:", error instanceof Error ? error.message : String(error));
    console.error("[API Route] Error stack:", error instanceof Error ? error.stack : "No stack");
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : "Failed to create API key",
        details: error instanceof Error ? error.stack : undefined
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    
    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }
    
    const response = await fetch(`${COLLECTOR_URL}/clerk/api-keys/me`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Collector API error:", response.status, errorText);
      return NextResponse.json(
        { error: errorText || `Collector API error: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch API keys:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to fetch API keys" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    
    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const keyId = searchParams.get("keyId");

    if (!keyId) {
      return NextResponse.json(
        { error: "keyId is required" },
        { status: 400 }
      );
    }

    const response = await fetch(`${COLLECTOR_URL}/clerk/api-keys/${keyId}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Collector API error:", response.status, errorText);
      return NextResponse.json(
        { error: errorText || `Collector API error: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to revoke API key:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to revoke API key" },
      { status: 500 }
    );
  }
}


import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const COLLECTOR_URL = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ tenantId: string }> }
) {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    
    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }
    
    const { tenantId } = await params;
    
    const response = await fetch(`${COLLECTOR_URL}/tenants/${tenantId}/customers`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Collector API error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch customer data:", error);
    return NextResponse.json(
      { error: "Failed to fetch customer data" },
      { status: 500 }
    );
  }
}


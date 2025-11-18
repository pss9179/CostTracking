import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || "", {
  apiVersion: "2024-11-20.acacia",
});

export async function POST(request: NextRequest) {
  try {
    const { getToken, userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { promoCode } = body;

    // Check if promo code is valid (hardcoded for now - you can make this dynamic)
    const validPromoCodes = ["FREETEST", "TEST2024", "BETA"];
    const isFree = promoCode && validPromoCodes.includes(promoCode.toUpperCase());

    if (isFree) {
      // For free promo codes, we'll handle it differently
      // You can create a subscription with $0 price or just mark user as having free access
      return NextResponse.json({ 
        success: true, 
        free: true,
        message: "Promo code applied! You have free access." 
      });
    }

    // Create Stripe checkout session
    const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
    const token = await getToken();
    
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ["card"],
      line_items: [
        {
          price_data: {
            currency: "usd",
            product_data: {
              name: "LLM Observe Pro",
              description: "Monthly subscription for LLM cost tracking",
            },
            recurring: {
              interval: "month",
            },
            unit_amount: 800, // $8.00
          },
          quantity: 1,
        },
      ],
      mode: "subscription",
      success_url: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/settings?success=true`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/settings?canceled=true`,
      client_reference_id: userId,
      metadata: {
        clerk_user_id: userId,
        promo_code: promoCode || "",
      },
    });

    return NextResponse.json({ url: session.url });
  } catch (error: any) {
    console.error("Stripe checkout error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to create checkout session" },
      { status: 500 }
    );
  }
}


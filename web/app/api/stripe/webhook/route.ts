import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { headers } from "next/headers";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || "sk_test_placeholder", {
  apiVersion: "2025-10-29.clover",
});

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET || "";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = (await headers()).get("stripe-signature");

  if (!signature) {
    return NextResponse.json({ error: "No signature" }, { status: 400 });
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err: any) {
    console.error("Webhook signature verification failed:", err.message);
    return NextResponse.json({ error: err.message }, { status: 400 });
  }

  const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";

  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        const clerkUserId = session.metadata?.clerk_user_id;
        
        if (clerkUserId) {
          // Update user subscription in backend
          await fetch(`${collectorUrl}/users/stripe/webhook`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              clerk_user_id: clerkUserId,
              stripe_customer_id: session.customer,
              stripe_subscription_id: session.subscription,
              subscription_status: "active",
            }),
          });
        }
        break;
      }

      case "customer.subscription.updated":
      case "customer.subscription.deleted": {
        const subscription = event.data.object as Stripe.Subscription;
        
        // Determine status based on subscription state
        let subscriptionStatus = "canceled";
        if (subscription.status === "active" || subscription.status === "trialing") {
          subscriptionStatus = "active";
        } else if (subscription.status === "past_due" || subscription.status === "unpaid") {
          subscriptionStatus = "past_due";
        }
        
        // Find user by subscription ID and update status
        await fetch(`${collectorUrl}/users/stripe/webhook`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            stripe_customer_id: subscription.customer as string,
            stripe_subscription_id: subscription.id,
            subscription_status: subscriptionStatus,
          }),
        });
        break;
      }
    }

    return NextResponse.json({ received: true });
  } catch (error: any) {
    console.error("Webhook handler error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}


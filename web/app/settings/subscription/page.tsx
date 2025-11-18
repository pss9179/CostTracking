"use client";

import { useState, useEffect } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { CheckCircle2, XCircle, CreditCard, Gift } from "lucide-react";
import { ProtectedLayout } from "@/components/ProtectedLayout";

export default function SubscriptionPage() {
  const { user } = useUser();
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [promoCode, setPromoCode] = useState("");
  const [promoError, setPromoError] = useState("");
  const [subscriptionStatus, setSubscriptionStatus] = useState<"free" | "active" | "canceled">("free");

  useEffect(() => {
    // Load subscription status
    loadSubscriptionStatus();
  }, []);

  const loadSubscriptionStatus = async () => {
    try {
      const token = await getToken();
      const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
      const response = await fetch(`${collectorUrl}/clerk/api-keys/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data.user?.subscription_status || "free");
      }
    } catch (error) {
      console.error("Failed to load subscription status:", error);
    }
  };

  const handleCheckout = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ promoCode }),
      });

      const data = await response.json();

      if (data.free) {
        // Apply free promo code
        const token = await getToken();
        const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
        await fetch(`${collectorUrl}/users/promo-code`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ promo_code: promoCode }),
        });
        setSubscriptionStatus("active");
        alert("Promo code applied! You now have free access.");
      } else if (data.url) {
        // Redirect to Stripe checkout
        window.location.href = data.url;
      } else {
        alert(data.error || "Failed to create checkout session");
      }
    } catch (error) {
      console.error("Checkout error:", error);
      alert("Failed to start checkout");
    } finally {
      setLoading(false);
    }
  };

  const handlePromoCode = async () => {
    if (!promoCode.trim()) {
      setPromoError("Please enter a promo code");
      return;
    }

    setLoading(true);
    setPromoError("");

    try {
      const response = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ promoCode: promoCode.trim() }),
      });

      const data = await response.json();

      if (data.free) {
        const token = await getToken();
        const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
        await fetch(`${collectorUrl}/users/promo-code`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ promo_code: promoCode.trim() }),
        });
        setSubscriptionStatus("active");
        setPromoCode("");
        alert("Promo code applied! You now have free access.");
      } else {
        setPromoError("Invalid promo code");
      }
    } catch (error) {
      setPromoError("Failed to apply promo code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedLayout>
      <div className="space-y-6 p-8">
        <div>
          <h1 className="text-3xl font-bold">Subscription</h1>
          <p className="text-gray-600 mt-2">Manage your subscription and billing</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Current Plan</CardTitle>
            <CardDescription>Your current subscription status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant={subscriptionStatus === "active" ? "default" : "secondary"}>
                    {subscriptionStatus === "active" ? (
                      <>
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Active
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3 h-3 mr-1" />
                        Free
                      </>
                    )}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {subscriptionStatus === "active"
                    ? "You have full access to all features"
                    : "Upgrade to Pro for $8/month to unlock all features"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {subscriptionStatus === "free" && (
          <>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Gift className="w-5 h-5" />
                  <CardTitle>Promo Code</CardTitle>
                </div>
                <CardDescription>Have a promo code? Enter it here for free access</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter promo code (e.g., FREETEST)"
                    value={promoCode}
                    onChange={(e) => {
                      setPromoCode(e.target.value);
                      setPromoError("");
                    }}
                    onKeyPress={(e) => e.key === "Enter" && handlePromoCode()}
                  />
                  <Button onClick={handlePromoCode} disabled={loading}>
                    Apply
                  </Button>
                </div>
                {promoError && (
                  <Alert variant="destructive">
                    <p className="text-sm">{promoError}</p>
                  </Alert>
                )}
                <p className="text-xs text-gray-500">
                  Valid promo codes: FREETEST, TEST2024, BETA
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  <CardTitle>Upgrade to Pro</CardTitle>
                </div>
                <CardDescription>$8/month - Cancel anytime</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="font-semibold">What's included:</h3>
                    <ul className="space-y-1 text-sm text-gray-600">
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span>Unlimited cost tracking</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span>Customer cost tracking</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span>Spending caps & alerts</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span>Advanced analytics</span>
                      </li>
                    </ul>
                  </div>
                  <Button onClick={handleCheckout} disabled={loading} className="w-full" size="lg">
                    {loading ? "Processing..." : "Subscribe for $8/month"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {subscriptionStatus === "active" && (
          <Card>
            <CardHeader>
              <CardTitle>Manage Subscription</CardTitle>
              <CardDescription>Cancel or update your subscription</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                To manage your subscription, visit your Stripe customer portal.
              </p>
              <Button variant="outline" onClick={() => {
                // You can add Stripe customer portal link here
                alert("Stripe customer portal integration coming soon");
              }}>
                Manage Subscription
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedLayout>
  );
}


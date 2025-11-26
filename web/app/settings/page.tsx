"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { 
  fetchPricingSettings, 
  updatePricingSettings, 
  fetchPricingOptions,
  PricingSettings,
  PricingOptions 
} from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Settings, DollarSign, Check, Loader2 } from "lucide-react";
import Sidebar from "@/components/Sidebar";

// Format plan name for display
function formatPlanName(plan: string): string {
  return plan
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function SettingsContent() {
  const { getToken } = useAuth();
  const [settings, setSettings] = useState<PricingSettings | null>(null);
  const [options, setOptions] = useState<PricingOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const token = await getToken();
        const [settingsData, optionsData] = await Promise.all([
          fetchPricingSettings(token || undefined),
          fetchPricingOptions(token || undefined),
        ]);
        setSettings(settingsData);
        setOptions(optionsData);
      } catch (err) {
        setError("Failed to load settings");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [getToken]);

  const handleSave = async () => {
    if (!settings) return;
    
    setSaving(true);
    setSaved(false);
    setError(null);

    try {
      const token = await getToken();
      await updatePricingSettings(settings, token || undefined);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError("Failed to save settings");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (key: keyof PricingSettings, value: string) => {
    if (settings) {
      setSettings({ ...settings, [key]: value });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error && !settings) {
    return (
      <div className="text-center text-red-500 p-8">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Settings className="h-6 w-6" />
            Settings
          </h1>
          <p className="text-gray-500 mt-1">
            Configure your pricing plans for accurate cost tracking
          </p>
        </div>
        <Button 
          onClick={handleSave} 
          disabled={saving}
          className="flex items-center gap-2"
        >
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : saved ? (
            <Check className="h-4 w-4" />
          ) : (
            <DollarSign className="h-4 w-4" />
          )}
          {saving ? "Saving..." : saved ? "Saved!" : "Save Settings"}
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Pricing Plans Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-green-600" />
            Pricing Plans
          </CardTitle>
          <CardDescription>
            Select your plan for each provider to ensure accurate cost calculations.
            Costs are calculated based on your selected tier.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {options && settings && (
            <>
              {/* Cartesia */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start p-4 bg-gray-50 rounded-lg">
                <div>
                  <Label className="text-base font-semibold">Cartesia</Label>
                  <p className="text-sm text-gray-500">Sonic TTS & Ink STT</p>
                </div>
                <div>
                  <Label htmlFor="cartesia-plan" className="text-sm text-gray-600">
                    Your Plan
                  </Label>
                  <Select
                    value={settings.cartesia_plan}
                    onValueChange={(value) => updateSetting("cartesia_plan", value)}
                  >
                    <SelectTrigger id="cartesia-plan" className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options.cartesia.options.map((plan) => (
                        <SelectItem key={plan} value={plan}>
                          {formatPlanName(plan)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="text-right">
                  <Label className="text-sm text-gray-600">Rate</Label>
                  <p className="text-lg font-semibold text-green-600 mt-1">
                    ${options.cartesia.rates[settings.cartesia_plan]?.toFixed(3) || "—"}
                    <span className="text-sm text-gray-500 font-normal ml-1">
                      / 1K chars
                    </span>
                  </p>
                </div>
              </div>

              {/* ElevenLabs */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start p-4 bg-gray-50 rounded-lg">
                <div>
                  <Label className="text-base font-semibold">ElevenLabs</Label>
                  <p className="text-sm text-gray-500">TTS & Scribe STT</p>
                </div>
                <div>
                  <Label htmlFor="elevenlabs-tier" className="text-sm text-gray-600">
                    Your Tier
                  </Label>
                  <Select
                    value={settings.elevenlabs_tier}
                    onValueChange={(value) => updateSetting("elevenlabs_tier", value)}
                  >
                    <SelectTrigger id="elevenlabs-tier" className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options.elevenlabs.options.map((tier) => (
                        <SelectItem key={tier} value={tier}>
                          {formatPlanName(tier)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="text-right">
                  <Label className="text-sm text-gray-600">Rate</Label>
                  <p className="text-lg font-semibold text-green-600 mt-1">
                    ${options.elevenlabs.rates[settings.elevenlabs_tier]?.toFixed(2) || "—"}
                    <span className="text-sm text-gray-500 font-normal ml-1">
                      / 1K chars
                    </span>
                  </p>
                </div>
              </div>

              {/* PlayHT */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start p-4 bg-gray-50 rounded-lg">
                <div>
                  <Label className="text-base font-semibold">PlayHT</Label>
                  <p className="text-sm text-gray-500">Play3.0 & PlayHT2.0 TTS</p>
                </div>
                <div>
                  <Label htmlFor="playht-plan" className="text-sm text-gray-600">
                    Your Plan
                  </Label>
                  <Select
                    value={settings.playht_plan}
                    onValueChange={(value) => updateSetting("playht_plan", value)}
                  >
                    <SelectTrigger id="playht-plan" className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options.playht.options.map((plan) => (
                        <SelectItem key={plan} value={plan}>
                          {formatPlanName(plan)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="text-right">
                  <Label className="text-sm text-gray-600">Rate</Label>
                  <p className="text-lg font-semibold text-green-600 mt-1">
                    ${options.playht.rates[settings.playht_plan]?.toFixed(3) || "—"}
                    <span className="text-sm text-gray-500 font-normal ml-1">
                      / 1K chars
                    </span>
                  </p>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <div className="text-blue-600 mt-0.5">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-blue-800">Why does this matter?</h3>
              <p className="text-sm text-blue-700 mt-1">
                Providers like Cartesia, ElevenLabs, and PlayHT have tiered pricing where 
                the cost per character/minute varies by plan. Selecting your actual plan 
                ensures your cost tracking is accurate. For pay-as-you-go providers like 
                Deepgram and Twilio, pricing is fixed and doesn't need configuration.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <SettingsContent />
      </main>
    </div>
  );
}

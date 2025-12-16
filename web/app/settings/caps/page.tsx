"use client";

import { useState, useEffect, useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { CapsManager } from "@/components/caps/CapsManager";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchProviderStats, fetchModelStats, fetchSectionStats } from "@/lib/api";
import { Shield, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function CapsSettingsPage() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [features, setFeatures] = useState<string[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        const token = await getToken();
        
        const [providersData, modelsData, sectionsData] = await Promise.all([
          fetchProviderStats(24 * 30, null, token || undefined).catch(() => []),
          fetchModelStats(24 * 30, null, token || undefined).catch(() => []),
          fetchSectionStats(24 * 30, null, token || undefined).catch(() => []),
        ]);
        
        setProviders(
          [...new Set(providersData.map(p => p.provider))]
            .filter(p => p !== "internal" && p !== "unknown")
        );
        setModels([...new Set(modelsData.map(m => m.model))]);
        setFeatures(
          [...new Set(sectionsData.map(s => s.section))]
            .filter(s => s !== "main" && s !== "default")
        );
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, [getToken]);

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="p-6 space-y-6">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-[400px] w-full rounded-xl" />
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link 
            href="/settings" 
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Shield className="w-6 h-6 text-blue-500" />
              Spending Caps & Alerts
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Set spending limits and receive alerts when thresholds are exceeded.
            </p>
          </div>
        </div>

        {/* Caps Manager */}
        <CapsManager
          providers={providers}
          models={models}
          features={features}
        />

        {/* Documentation */}
        <div className="bg-gray-50 rounded-xl p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">How Caps Work</h3>
          
          <div className="grid md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Cap Types</h4>
              <ul className="space-y-2 text-gray-600">
                <li><strong>Global:</strong> Applies to all API calls across all providers</li>
                <li><strong>Provider:</strong> Limits spend on a specific provider (OpenAI, Anthropic, etc.)</li>
                <li><strong>Model:</strong> Limits spend on a specific model (gpt-4o, claude-3-opus, etc.)</li>
                <li><strong>Feature:</strong> Limits spend on a labeled feature or agent in your code</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Enforcement Options</h4>
              <ul className="space-y-2 text-gray-600">
                <li><strong>Alert Only:</strong> Send email notification when threshold is reached (default)</li>
                <li><strong>Hard Block:</strong> Reject API calls when limit is exceeded (requires SDK integration)</li>
              </ul>
            </div>
          </div>
          
          <div className="pt-4 border-t">
            <h4 className="font-medium text-gray-900 mb-2">Alert Threshold</h4>
            <p className="text-sm text-gray-600">
              Set the percentage of the limit at which you want to receive an alert. 
              For example, setting 80% on a $100 limit will alert you when spend reaches $80.
            </p>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}


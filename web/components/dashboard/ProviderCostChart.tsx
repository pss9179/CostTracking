"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface ProviderCostChartProps {
  data: Array<{
    date: string;
    [provider: string]: string | number;
  }>;
  providers: string[];
}

// Color scheme per spec: LLM (blue), Vector DB (orange), API (purple), Agent (slate)
const PROVIDER_COLORS: Record<string, string> = {
  openai: "#3b82f6",      // LLM - blue
  anthropic: "#10b981",   // LLM - green
  google: "#06b6d4",      // LLM - cyan
  cohere: "#8b5cf6",      // LLM - violet
  pinecone: "#f97316",    // Vector DB - orange
  weaviate: "#ea580c",    // Vector DB - orange
  qdrant: "#fb923c",      // Vector DB - lighter orange
  milvus: "#fdba74",      // Vector DB - lightest orange
  stripe: "#a855f7",      // API - purple
  twilio: "#9333ea",      // API - darker purple
  elevenlabs: "#c084fc",  // API - lighter purple
};

function getProviderColor(provider: string): string {
  return PROVIDER_COLORS[provider.toLowerCase()] || "#64748b"; // Default to slate
}

export function ProviderCostChart({ data, providers }: ProviderCostChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Total Spend by Provider (Daily)</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="h-64 flex items-center justify-center">
            <p className="text-muted-foreground">No cost data available</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                formatter={(value: number) => [`$${value.toFixed(4)}`, ""]}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Legend />
              {providers.map((provider) => (
                <Area
                  key={provider}
                  type="monotone"
                  dataKey={provider}
                  stackId="1"
                  stroke={getProviderColor(provider)}
                  fill={getProviderColor(provider)}
                  fillOpacity={0.6}
                  name={provider}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}


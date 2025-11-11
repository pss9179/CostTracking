"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import { formatCost } from "@/lib/stats";

interface CostTrendData {
  date: string;
  openai?: number;
  pinecone?: number;
  anthropic?: number;
  [key: string]: any;
}

interface CostTrendChartProps {
  data: CostTrendData[];
  height?: number;
}

const PROVIDER_COLORS = {
  openai: "#3b82f6",      // blue
  pinecone: "#a855f7",    // purple
  anthropic: "#f97316",   // orange
  default: "#6b7280",     // gray
};

export function CostTrendChart({ data, height = 300 }: CostTrendChartProps) {
  // Get all unique providers from the data
  const providers = Array.from(
    new Set(
      data.flatMap((d) =>
        Object.keys(d).filter((k) => k !== "date" && typeof d[k] === "number")
      )
    )
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => format(new Date(value), "MMM d")}
          className="text-xs"
        />
        <YAxis
          tickFormatter={(value) => formatCost(value)}
          className="text-xs"
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;

            return (
              <div className="bg-background border rounded-lg p-3 shadow-lg">
                <p className="font-medium mb-2">
                  {format(new Date(label), "MMM d, yyyy")}
                </p>
                <div className="space-y-1">
                  {payload.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: entry.color }}
                      />
                      <span className="capitalize">{entry.name}:</span>
                      <span className="font-semibold">{formatCost(Number(entry.value))}</span>
                    </div>
                  ))}
                  <div className="pt-1 mt-1 border-t">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <span>Total:</span>
                      <span>
                        {formatCost(
                          payload.reduce((sum, entry) => sum + Number(entry.value), 0)
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          }}
        />
        <Legend
          wrapperStyle={{ paddingTop: "20px" }}
          formatter={(value) => <span className="capitalize">{value}</span>}
        />
        {providers.map((provider) => (
          <Line
            key={provider}
            type="monotone"
            dataKey={provider}
            stroke={PROVIDER_COLORS[provider as keyof typeof PROVIDER_COLORS] || PROVIDER_COLORS.default}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            name={provider}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}


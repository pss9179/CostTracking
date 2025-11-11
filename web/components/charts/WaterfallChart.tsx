"use client";

import { useMemo } from "react";
import { formatCost, formatDuration } from "@/lib/stats";
import { Badge } from "@/components/ui/badge";

interface WaterfallEvent {
  id: string;
  section: string;
  section_path: string | null;
  provider: string;
  endpoint: string;
  model: string | null;
  cost_usd: number;
  latency_ms: number;
  status: string;
  created_at: string;
}

interface WaterfallChartProps {
  events: WaterfallEvent[];
  height?: number;
}

export function WaterfallChart({ events, height = 400 }: WaterfallChartProps) {
  // Calculate timeline data
  const timelineData = useMemo(() => {
    if (events.length === 0) return { events: [], minTime: 0, maxTime: 0, duration: 0 };

    // Sort events by timestamp
    const sorted = [...events].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    const minTime = new Date(sorted[0].created_at).getTime();
    const maxTime = new Date(sorted[sorted.length - 1].created_at).getTime() + sorted[sorted.length - 1].latency_ms;
    const duration = maxTime - minTime;

    const mappedEvents = sorted.map((event, index) => {
      const startTime = new Date(event.created_at).getTime();
      const startOffset = startTime - minTime;
      const widthPercent = duration > 0 ? (event.latency_ms / duration) * 100 : 0;
      const leftPercent = duration > 0 ? (startOffset / duration) * 100 : 0;

      return {
        ...event,
        index,
        startOffset,
        widthPercent: Math.max(widthPercent, 0.5), // Minimum 0.5% width for visibility
        leftPercent,
      };
    });

    return { events: mappedEvents, minTime, maxTime, duration };
  }, [events]);

  const { events: timelineEvents, duration } = timelineData;

  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No events to display
      </div>
    );
  }

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      openai: "bg-blue-500",
      pinecone: "bg-purple-500",
      anthropic: "bg-orange-500",
    };
    return colors[provider.toLowerCase()] || "bg-gray-500";
  };

  return (
    <div className="space-y-4">
      {/* Timeline Header */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>Start</span>
        <span>Total Duration: {formatDuration(duration)}</span>
        <span>End</span>
      </div>

      {/* Waterfall Bars */}
      <div
        className="space-y-2 overflow-y-auto"
        style={{ maxHeight: `${height}px` }}
      >
        {timelineEvents.map((event) => (
          <div key={event.id} className="relative">
            {/* Event Row */}
            <div className="flex items-center gap-3 min-h-[48px]">
              {/* Label */}
              <div className="w-48 flex-shrink-0 text-xs">
                <Badge variant="secondary" className="mb-1">
                  {event.section_path || event.section}
                </Badge>
                <div className="text-muted-foreground">
                  {event.provider} · {event.model || event.endpoint}
                </div>
              </div>

              {/* Timeline Bar Container */}
              <div className="flex-1 relative h-8 bg-muted/30 rounded">
                {/* Timeline Bar */}
                <div
                  className={`absolute h-full rounded flex items-center justify-between px-2 ${getProviderColor(
                    event.provider
                  )} hover:opacity-90 transition-opacity cursor-pointer group`}
                  style={{
                    left: `${event.leftPercent}%`,
                    width: `${event.widthPercent}%`,
                  }}
                  title={`${event.section} - ${formatDuration(event.latency_ms)} - ${formatCost(
                    event.cost_usd
                  )}`}
                >
                  <span className="text-xs text-white font-medium truncate">
                    {formatDuration(event.latency_ms)}
                  </span>
                  <span className="text-xs text-white/90">
                    {formatCost(event.cost_usd)}
                  </span>
                </div>
              </div>

              {/* Status Indicator */}
              <div className="w-16 flex-shrink-0 text-xs text-right">
                <Badge
                  variant={event.status === "ok" ? "default" : "destructive"}
                  className="text-xs"
                >
                  {event.status}
                </Badge>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 pt-4 border-t text-xs">
        <span className="text-muted-foreground font-medium">Providers:</span>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-500" />
          <span>OpenAI</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-purple-500" />
          <span>Pinecone</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-orange-500" />
          <span>Anthropic</span>
        </div>
      </div>
    </div>
  );
}


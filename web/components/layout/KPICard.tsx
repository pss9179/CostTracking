import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  icon?: LucideIcon;
  change?: number; // Percentage change
  changeLabel?: string; // e.g., "vs last 7d"
  trend?: "up" | "down" | "neutral";
  invertColors?: boolean; // If true, up = bad (red), down = good (green)
  description?: string;
  className?: string;
}

export function KPICard({
  title,
  value,
  icon: Icon,
  change,
  changeLabel = "vs previous period",
  trend,
  invertColors = false,
  description,
  className,
}: KPICardProps) {
  // Auto-determine trend from change if not provided
  const actualTrend = trend || (change !== undefined
    ? change > 0
      ? "up"
      : change < 0
      ? "down"
      : "neutral"
    : "neutral");

  // Determine colors based on trend and inversion
  const isGood = invertColors
    ? actualTrend === "down"
    : actualTrend === "up";
  const isBad = invertColors
    ? actualTrend === "up"
    : actualTrend === "down";

  const trendColor = isGood
    ? "text-green-600"
    : isBad
    ? "text-red-600"
    : "text-gray-600";

  const TrendIcon =
    actualTrend === "up"
      ? TrendingUp
      : actualTrend === "down"
      ? TrendingDown
      : Minus;

  return (
    <Card className={cn("border-gray-200 bg-white", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        {Icon && <Icon className="h-4 w-4 text-gray-400" />}
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div className="text-3xl font-bold text-gray-900">{value}</div>
          {change !== undefined && (
            <div className={cn("flex items-center text-xs font-medium", trendColor)}>
              <TrendIcon className="mr-1 h-3.5 w-3.5" />
              <span>
                {change > 0 ? "+" : ""}
                {change.toFixed(1)}%
              </span>
              <span className="ml-1.5 text-gray-500 font-normal">{changeLabel}</span>
            </div>
          )}
          {description && (
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}


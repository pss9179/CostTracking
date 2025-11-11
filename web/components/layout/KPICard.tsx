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
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          <div className="text-2xl font-bold">{value}</div>
          {change !== undefined && (
            <div className={cn("flex items-center text-xs", trendColor)}>
              <TrendIcon className="mr-1 h-3 w-3" />
              <span className="font-medium">
                {change > 0 ? "+" : ""}
                {change.toFixed(1)}%
              </span>
              <span className="ml-1 text-muted-foreground">{changeLabel}</span>
            </div>
          )}
          {description && (
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}


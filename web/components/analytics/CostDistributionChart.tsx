"use client";

import { useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Treemap,
} from "recharts";
import { cn } from "@/lib/utils";
import {
  formatSmartCost,
  formatPercentage,
  getStableColor,
  getTopNWithOther,
} from "@/lib/format";

// ============================================================================
// TYPES
// ============================================================================

export interface CostItem {
  name: string;
  cost: number;
  calls?: number;
  avgLatency?: number;
  p95Latency?: number;
  costPerCall?: number;
  p50CostPerCall?: number;
  p95CostPerCall?: number;
  [key: string]: any;
}

interface CostDistributionChartProps {
  data: CostItem[];
  totalCost: number;
  topN?: number;
  height?: number;
  onClick?: (item: CostItem) => void;
  className?: string;
  colorKey?: string;
}

type ViewMode = "absolute" | "percentage";

// ============================================================================
// SEMANTIC COLOR SYSTEM
// ============================================================================

// Cost = neutral blue (consistent across all cost visualizations)
const COST_COLOR = "#3b82f6"; // blue-500
const COST_COLOR_LIGHT = "#93c5fd"; // blue-300
const OTHER_COLOR = "#94a3b8"; // slate-400

// ============================================================================
// VIEW MODE TOGGLE
// ============================================================================

interface ViewModeToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

function ViewModeToggle({ mode, onChange }: ViewModeToggleProps) {
  return (
    <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
      <button
        onClick={() => onChange("absolute")}
        className={cn(
          "px-2.5 py-1 text-xs font-medium rounded-md transition-all",
          mode === "absolute"
            ? "bg-white text-slate-900 shadow-sm"
            : "text-slate-500 hover:text-slate-700"
        )}
      >
        $ Value
      </button>
      <button
        onClick={() => onChange("percentage")}
        className={cn(
          "px-2.5 py-1 text-xs font-medium rounded-md transition-all",
          mode === "percentage"
            ? "bg-white text-slate-900 shadow-sm"
            : "text-slate-500 hover:text-slate-700"
        )}
      >
        % of Total
      </button>
    </div>
  );
}

// ============================================================================
// CUSTOM TOOLTIP
// ============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  totalCost: number;
  showVariance?: boolean;
}

function CustomTooltip({
  active,
  payload,
  totalCost,
  showVariance,
}: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-xl text-sm min-w-[160px]">
      <p className="font-medium capitalize mb-1.5 text-white">
        {data.isOther && data.otherCount
          ? `${data.otherCount} other categories`
          : data.displayName || data.name}
      </p>
      <div className="space-y-1 text-xs">
        <p className="flex justify-between gap-4">
          <span className="text-slate-400">Cost:</span>
          <span className="font-medium tabular-nums text-white">
            {formatSmartCost(data.cost)}
          </span>
        </p>
        <p className="flex justify-between gap-4">
          <span className="text-slate-400">Share:</span>
          <span className="font-medium">
            {formatPercentage(
              totalCost > 0 ? (data.cost / totalCost) * 100 : 0
            )}
          </span>
        </p>
        {data.calls !== undefined && data.calls > 0 && (
          <>
            <p className="flex justify-between gap-4">
              <span className="text-slate-400">Calls:</span>
              <span className="font-medium tabular-nums">
                {data.calls.toLocaleString()}
              </span>
            </p>
            <p className="flex justify-between gap-4">
              <span className="text-slate-400">Cost/call:</span>
              <span className="font-medium tabular-nums">
                {formatSmartCost(data.cost / data.calls)}
              </span>
            </p>
          </>
        )}
        {/* Variance insight: p50/p95 cost per request */}
        {showVariance && data.p50CostPerCall !== undefined && (
          <div className="mt-1.5 pt-1.5 border-t border-slate-700">
            <p className="text-slate-400 mb-1">Cost/request variance:</p>
            <p className="flex justify-between gap-4">
              <span className="text-slate-400">p50:</span>
              <span className="font-medium tabular-nums">
                {formatSmartCost(data.p50CostPerCall)}
              </span>
            </p>
            <p className="flex justify-between gap-4">
              <span className="text-slate-400">p95:</span>
              <span className="font-medium tabular-nums text-amber-400">
                {formatSmartCost(data.p95CostPerCall)}
              </span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// RANKED HORIZONTAL BAR CHART (PRIMARY)
// ============================================================================

interface RankedBarChartProps {
  data: CostItem[];
  totalCost: number;
  topN?: number;
  height?: number;
  onClick?: (item: CostItem) => void;
  className?: string;
  colorKey?: string;
  showToggle?: boolean;
  showVariance?: boolean;
}

export function RankedBarChart({
  data,
  totalCost,
  topN = 8,
  height = 240,
  onClick,
  className,
  colorKey = "name",
  showToggle = true,
  showVariance = false,
}: RankedBarChartProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("absolute");

  // Split into top N + other, sorted by cost desc
  const chartData = useMemo(() => {
    const sorted = [...data].sort((a, b) => b.cost - a.cost);
    const { topN: topItems, hasOther, other, otherTotal } = getTopNWithOther(
      sorted,
      topN,
      (item) => item.cost
    );

    const items = topItems.map((item) => ({
      ...item,
      displayName:
        item.name.length > 25 ? item.name.slice(0, 22) + "..." : item.name,
      value:
        viewMode === "absolute"
          ? item.cost
          : totalCost > 0
          ? (item.cost / totalCost) * 100
          : 0,
      percentage: totalCost > 0 ? (item.cost / totalCost) * 100 : 0,
      color: getStableColor(item[colorKey] || item.name),
      isOther: false,
      originalItem: item,
    }));

    if (hasOther && otherTotal > 0) {
      items.push({
        name: "Other",
        displayName: `+${other.length} others`,
        cost: otherTotal,
        calls: other.reduce((sum, item) => sum + (item.calls || 0), 0),
        value:
          viewMode === "absolute"
            ? otherTotal
            : totalCost > 0
            ? (otherTotal / totalCost) * 100
            : 0,
        percentage: totalCost > 0 ? (otherTotal / totalCost) * 100 : 0,
        color: OTHER_COLOR,
        isOther: true,
        otherCount: other.length,
        originalItem: null,
      } as any);
    }

    return items;
  }, [data, topN, totalCost, viewMode, colorKey]);

  if (data.length === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center bg-slate-50 rounded-lg",
          className
        )}
        style={{ height }}
      >
        <p className="text-sm text-slate-400">No data available</p>
      </div>
    );
  }

  // Calculate dynamic bar height based on number of items
  const barHeight = Math.max(20, Math.min(32, (height - 40) / chartData.length));
  const chartHeight = Math.max(height, chartData.length * barHeight + 40);

  return (
    <div className={cn("relative", className)}>
      {showToggle && (
        <div className="flex justify-end mb-3">
          <ViewModeToggle mode={viewMode} onChange={setViewMode} />
        </div>
      )}

      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 8, left: 4, bottom: 4 }}
          barCategoryGap={4}
        >
          <XAxis
            type="number"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickFormatter={(value) =>
              viewMode === "absolute"
                ? formatSmartCost(value)
                : `${value.toFixed(0)}%`
            }
            domain={viewMode === "percentage" ? [0, 100] : undefined}
          />
          <YAxis
            type="category"
            dataKey="displayName"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#64748b", fontSize: 11 }}
            width={120}
          />
          <Tooltip
            content={
              <CustomTooltip
                totalCost={totalCost}
                showVariance={showVariance}
              />
            }
            cursor={{ fill: "#f1f5f9" }}
          />
          <Bar
            dataKey="value"
            radius={[0, 4, 4, 0]}
            cursor={onClick ? "pointer" : "default"}
            onClick={(data) => {
              if (onClick && data.originalItem) {
                onClick(data.originalItem);
              }
            }}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.isOther ? OTHER_COLOR : COST_COLOR}
                fillOpacity={entry.isOther ? 0.6 : 0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================================
// LEGACY TREEMAP (kept for compatibility)
// ============================================================================

interface TreemapContentProps {
  x: number;
  y: number;
  width: number;
  height: number;
  name: string;
  value: number;
  color: string;
  percentage: number;
  isOther?: boolean;
  otherCount?: number;
  onClick?: () => void;
}

function TreemapContent({
  x,
  y,
  width,
  height,
  name,
  value,
  color,
  percentage,
  isOther,
  otherCount,
  onClick,
}: TreemapContentProps) {
  const showLabel = width > 60 && height > 40;
  const showValue = width > 80 && height > 55;
  const showPercent = width > 50 && height > 30;

  const displayName =
    isOther && otherCount
      ? `+${otherCount} others`
      : name.length > 15 && width < 120
      ? name.slice(0, 12) + "..."
      : name;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={color}
        stroke="white"
        strokeWidth={2}
        rx={4}
        className={cn(
          "transition-opacity cursor-pointer",
          onClick && "hover:opacity-80"
        )}
        onClick={onClick}
      />
      {showLabel && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - (showValue ? 8 : 0)}
            textAnchor="middle"
            fill="white"
            className="text-xs font-medium capitalize pointer-events-none"
            style={{ textShadow: "0 1px 2px rgba(0,0,0,0.3)" }}
          >
            {displayName}
          </text>
          {showValue && (
            <text
              x={x + width / 2}
              y={y + height / 2 + 10}
              textAnchor="middle"
              fill="white"
              className="text-xs pointer-events-none opacity-90"
              style={{ textShadow: "0 1px 2px rgba(0,0,0,0.3)" }}
            >
              {formatSmartCost(value)}
            </text>
          )}
        </>
      )}
      {!showLabel && showPercent && (
        <text
          x={x + width / 2}
          y={y + height / 2 + 4}
          textAnchor="middle"
          fill="white"
          className="text-[10px] font-medium pointer-events-none"
          style={{ textShadow: "0 1px 2px rgba(0,0,0,0.3)" }}
        >
          {formatPercentage(percentage)}
        </text>
      )}
    </g>
  );
}

interface LegacyTooltipProps {
  active?: boolean;
  payload?: any[];
}

function LegacyTooltip({ active, payload }: LegacyTooltipProps) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-xl text-sm">
      <p className="font-medium capitalize mb-1">
        {data.isOther && data.otherCount
          ? `${data.otherCount} other categories`
          : data.name}
      </p>
      <div className="space-y-0.5 text-xs">
        <p className="flex justify-between gap-4">
          <span className="text-slate-400">Cost:</span>
          <span className="font-medium tabular-nums">
            {formatSmartCost(data.value)}
          </span>
        </p>
        <p className="flex justify-between gap-4">
          <span className="text-slate-400">Share:</span>
          <span className="font-medium">{formatPercentage(data.percentage)}</span>
        </p>
        {data.calls !== undefined && (
          <p className="flex justify-between gap-4">
            <span className="text-slate-400">Calls:</span>
            <span className="font-medium tabular-nums">
              {data.calls.toLocaleString()}
            </span>
          </p>
        )}
      </div>
    </div>
  );
}

export function CostDistributionChart({
  data,
  totalCost,
  topN = 8,
  height = 200,
  onClick,
  className,
  colorKey = "name",
}: CostDistributionChartProps) {
  // Split into top N + other
  const { topN: topItems, hasOther, other, otherTotal } = useMemo(() => {
    return getTopNWithOther(data, topN, (item) => item.cost);
  }, [data, topN]);

  // Prepare treemap data
  const treemapData = useMemo(() => {
    const items = topItems.map((item) => ({
      name: item.name,
      value: item.cost,
      calls: item.calls,
      percentage: totalCost > 0 ? (item.cost / totalCost) * 100 : 0,
      color: getStableColor(item[colorKey] || item.name),
      isOther: false,
      originalItem: item,
    }));

    if (hasOther && otherTotal > 0) {
      items.push({
        name: "Other",
        value: otherTotal,
        calls: other.reduce((sum, item) => sum + (item.calls || 0), 0),
        percentage: totalCost > 0 ? (otherTotal / totalCost) * 100 : 0,
        color: "#94a3b8", // slate-400
        isOther: true,
        otherCount: other.length,
        originalItem: null,
      } as any);
    }

    return items;
  }, [topItems, hasOther, other, otherTotal, totalCost, colorKey]);

  if (data.length === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center bg-slate-50 rounded-lg",
          className
        )}
        style={{ height }}
      >
        <p className="text-sm text-slate-400">No data available</p>
      </div>
    );
  }

  return (
    <div className={cn("relative", className)}>
      <ResponsiveContainer width="100%" height={height}>
        <Treemap
          data={treemapData}
          dataKey="value"
          aspectRatio={4 / 3}
          stroke="white"
          animationDuration={300}
          content={({ x, y, width, height, index }: any) => {
            const item = treemapData[index];
            if (!item) {
              return <g key={`empty-${index}`} />;
            }

            return (
              <TreemapContent
                key={`content-${index}`}
                x={x}
                y={y}
                width={width}
                height={height}
                name={item.name}
                value={item.value}
                color={item.color}
                percentage={item.percentage}
                isOther={item.isOther}
                otherCount={(item as any).otherCount}
                onClick={
                  onClick && item.originalItem
                    ? () => onClick(item.originalItem)
                    : undefined
                }
              />
            );
          }}
        >
          <Tooltip content={<LegacyTooltip />} />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================================
// STACKED BAR (horizontal pill style)
// ============================================================================

interface StackedBarChartProps {
  data: CostItem[];
  totalCost: number;
  topN?: number;
  height?: number;
  onClick?: (item: CostItem) => void;
  className?: string;
}

export function StackedBarChart({
  data,
  totalCost,
  topN = 8,
  height = 24,
  onClick,
  className,
}: StackedBarChartProps) {
  const { topN: topItems, hasOther, other, otherTotal } = useMemo(() => {
    return getTopNWithOther(data, topN, (item) => item.cost);
  }, [data, topN]);

  const segments = useMemo(() => {
    const items = topItems.map((item) => ({
      name: item.name,
      cost: item.cost,
      percentage: totalCost > 0 ? (item.cost / totalCost) * 100 : 0,
      color: getStableColor(item.name),
      isOther: false,
      originalItem: item,
    }));

    if (hasOther && otherTotal > 0) {
      items.push({
        name: "Other",
        cost: otherTotal,
        percentage: totalCost > 0 ? (otherTotal / totalCost) * 100 : 0,
        color: "#94a3b8",
        isOther: true,
        originalItem: null,
        otherCount: other.length,
      } as any);
    }

    return items;
  }, [topItems, hasOther, other, otherTotal, totalCost]);

  if (data.length === 0) {
    return (
      <div
        className={cn("rounded-full bg-slate-100", className)}
        style={{ height }}
      />
    );
  }

  return (
    <div
      className={cn("flex rounded-full overflow-hidden", className)}
      style={{ height }}
    >
      {segments.map((segment, i) => (
        <div
          key={segment.name}
          className={cn(
            "transition-all cursor-pointer hover:opacity-80",
            i === 0 && "rounded-l-full",
            i === segments.length - 1 && "rounded-r-full"
          )}
          style={{
            width: `${Math.max(segment.percentage, 0.5)}%`,
            backgroundColor: segment.color,
          }}
          title={`${segment.name}: ${formatSmartCost(segment.cost)} (${formatPercentage(segment.percentage)})`}
          onClick={() => !segment.isOther && onClick?.(segment.originalItem!)}
        />
      ))}
    </div>
  );
}

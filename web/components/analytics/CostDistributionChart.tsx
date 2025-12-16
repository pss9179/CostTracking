"use client";

import { useMemo, useState } from "react";
import { Treemap, ResponsiveContainer, Tooltip } from "recharts";
import { cn } from "@/lib/utils";
import { formatSmartCost, formatPercentage, getStableColor, getTopNWithOther } from "@/lib/format";

// ============================================================================
// TYPES
// ============================================================================

interface CostItem {
  name: string;
  cost: number;
  calls?: number;
  [key: string]: any;
}

interface CostDistributionChartProps {
  data: CostItem[];
  totalCost: number;
  topN?: number;
  height?: number;
  onClick?: (item: CostItem) => void;
  className?: string;
  colorKey?: string; // Which field to use for stable color (default: name)
}

// ============================================================================
// TREEMAP CONTENT
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
  
  const displayName = isOther && otherCount
    ? `+${otherCount} others`
    : name.length > 15 && width < 120
      ? name.slice(0, 12) + '...'
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
            style={{ textShadow: '0 1px 2px rgba(0,0,0,0.3)' }}
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
              style={{ textShadow: '0 1px 2px rgba(0,0,0,0.3)' }}
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
          style={{ textShadow: '0 1px 2px rgba(0,0,0,0.3)' }}
        >
          {formatPercentage(percentage)}
        </text>
      )}
    </g>
  );
}

// ============================================================================
// TOOLTIP
// ============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
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
          <span className="font-medium tabular-nums">{formatSmartCost(data.value)}</span>
        </p>
        <p className="flex justify-between gap-4">
          <span className="text-slate-400">Share:</span>
          <span className="font-medium">{formatPercentage(data.percentage)}</span>
        </p>
        {data.calls !== undefined && (
          <p className="flex justify-between gap-4">
            <span className="text-slate-400">Calls:</span>
            <span className="font-medium tabular-nums">{data.calls.toLocaleString()}</span>
          </p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function CostDistributionChart({
  data,
  totalCost,
  topN = 8,
  height = 200,
  onClick,
  className,
  colorKey = 'name',
}: CostDistributionChartProps) {
  // Split into top N + other
  const { topN: topItems, hasOther, other, otherTotal } = useMemo(() => {
    return getTopNWithOther(data, topN, item => item.cost);
  }, [data, topN]);
  
  // Prepare treemap data
  const treemapData = useMemo(() => {
    const items = topItems.map(item => ({
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
        name: 'Other',
        value: otherTotal,
        calls: other.reduce((sum, item) => sum + (item.calls || 0), 0),
        percentage: totalCost > 0 ? (otherTotal / totalCost) * 100 : 0,
        color: '#94a3b8', // slate-400
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
        className={cn("flex items-center justify-center bg-slate-50 rounded-lg", className)}
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
          aspectRatio={4/3}
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
                onClick={onClick && item.originalItem ? () => onClick(item.originalItem) : undefined}
              />
            );
          }}
        >
          <Tooltip content={<CustomTooltip />} />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================================
// STACKED BAR ALTERNATIVE (for comparison)
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
    return getTopNWithOther(data, topN, item => item.cost);
  }, [data, topN]);
  
  const segments = useMemo(() => {
    const items = topItems.map(item => ({
      name: item.name,
      cost: item.cost,
      percentage: totalCost > 0 ? (item.cost / totalCost) * 100 : 0,
      color: getStableColor(item.name),
      isOther: false,
      originalItem: item,
    }));
    
    if (hasOther && otherTotal > 0) {
      items.push({
        name: 'Other',
        cost: otherTotal,
        percentage: totalCost > 0 ? (otherTotal / totalCost) * 100 : 0,
        color: '#94a3b8',
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


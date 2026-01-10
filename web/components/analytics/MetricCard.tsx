"use client";

import { ReactNode } from "react";
import { TrendingUp, TrendingDown, Minus, Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { formatSmartCost, formatPercentChange, type PercentChange } from "@/lib/format";

// ============================================================================
// TYPES
// ============================================================================

interface MetricCardProps {
  // Content
  title: string;
  value: string | number;
  subtitle?: string;
  
  // Delta/comparison
  previousValue?: number;
  delta?: PercentChange;
  deltaLabel?: string; // e.g., "vs yesterday"
  
  // Formatting
  formatValue?: (value: number) => string;
  
  // Tooltip for full precision
  tooltipContent?: ReactNode;
  
  // Icon
  icon?: ReactNode;
  
  // Styling
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// ============================================================================
// VARIANT STYLES
// ============================================================================

const VARIANT_STYLES = {
  default: {
    container: "bg-white border border-slate-200/60",
    title: "text-slate-500",
    value: "text-slate-900",
    icon: "text-slate-400",
  },
  primary: {
    container: "bg-gradient-to-br from-slate-900 to-slate-800 text-white border-0",
    title: "text-slate-400",
    value: "text-white",
    icon: "text-emerald-400",
  },
  success: {
    container: "bg-emerald-50 border border-emerald-200/60",
    title: "text-emerald-600",
    value: "text-emerald-900",
    icon: "text-emerald-500",
  },
  warning: {
    container: "bg-amber-50 border border-amber-200/60",
    title: "text-amber-600",
    value: "text-amber-900",
    icon: "text-amber-500",
  },
  danger: {
    container: "bg-rose-50 border border-rose-200/60",
    title: "text-rose-600",
    value: "text-rose-900",
    icon: "text-rose-500",
  },
  info: {
    container: "bg-blue-50 border border-blue-200/60",
    title: "text-blue-600",
    value: "text-blue-900",
    icon: "text-blue-500",
  },
};

const SIZE_STYLES = {
  sm: {
    padding: "p-3",
    title: "text-xs",
    value: "text-lg",
    icon: "w-3.5 h-3.5",
  },
  md: {
    padding: "p-4",
    title: "text-xs",
    value: "text-2xl",
    icon: "w-4 h-4",
  },
  lg: {
    padding: "p-5",
    title: "text-sm",
    value: "text-3xl",
    icon: "w-5 h-5",
  },
};

// ============================================================================
// DELTA BADGE
// ============================================================================

interface DeltaBadgeProps {
  delta: PercentChange;
  variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info';
}

function DeltaBadge({ delta, variant }: DeltaBadgeProps) {
  const isPrimary = variant === 'primary';
  
  if (delta.direction === 'flat') {
    return (
      <span className={cn(
        "flex items-center gap-1 text-xs font-medium",
        isPrimary ? "text-slate-400" : "text-slate-400"
      )}>
        <Minus className="w-3 h-3" />
        {delta.formatted}
      </span>
    );
  }
  
  const isUp = delta.direction === 'up';
  
  // For cost metrics, up is bad (rose), down is good (emerald)
  // Reversed from typical metrics
  const colorClass = isPrimary
    ? isUp ? "text-rose-400" : "text-emerald-400"
    : isUp ? "text-rose-500" : "text-emerald-500";
  
  return (
    <span className={cn("flex items-center gap-0.5 text-xs font-medium", colorClass)}>
      {isUp ? (
        <TrendingUp className="w-3.5 h-3.5" />
      ) : (
        <TrendingDown className="w-3.5 h-3.5" />
      )}
      {delta.formatted}
    </span>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function MetricCard({
  title,
  value,
  subtitle,
  previousValue,
  delta: providedDelta,
  deltaLabel = "vs previous",
  formatValue,
  tooltipContent,
  icon,
  variant = 'default',
  size = 'md',
  className,
}: MetricCardProps) {
  const styles = VARIANT_STYLES[variant];
  const sizeStyles = SIZE_STYLES[size];
  
  // Calculate delta if not provided but previousValue is
  const delta = providedDelta ?? (
    typeof value === 'number' && previousValue !== undefined
      ? formatPercentChange(value, previousValue)
      : undefined
  );
  
  // Format the value
  const displayValue = typeof value === 'number'
    ? (formatValue ? formatValue(value) : formatSmartCost(value))
    : value;
  
  // Full precision value for tooltip
  const fullPrecisionValue = typeof value === 'number'
    ? formatSmartCost(value, { precision: 'full' })
    : value;
  
  const content = (
    <div className={cn(
      "rounded-xl transition-all",
      styles.container,
      sizeStyles.padding,
      className
    )}>
      {/* Header row */}
      <div className="flex items-center gap-2 mb-1">
        {icon && (
          <span className={cn(styles.icon, sizeStyles.icon)}>
            {icon}
          </span>
        )}
        <span className={cn(
          "font-medium uppercase tracking-wide",
          styles.title,
          sizeStyles.title
        )}>
          {title}
        </span>
      </div>
      
      {/* Value row */}
      <div className="flex items-baseline gap-3">
        <span className={cn(
          "font-bold tracking-tight tabular-nums",
          styles.value,
          sizeStyles.value
        )}>
          {displayValue}
        </span>
        
        {/* Delta indicator */}
        {delta && <DeltaBadge delta={delta} variant={variant} />}
      </div>
      
      {/* Subtitle / Delta label */}
      {(subtitle || (delta && deltaLabel)) && (
        <p className={cn(
          "text-xs mt-1",
          variant === 'primary' ? "text-slate-400" : "text-slate-400"
        )}>
          {subtitle || deltaLabel}
        </p>
      )}
    </div>
  );
  
  // Wrap with tooltip if content provided or we have full precision
  if (tooltipContent || (typeof value === 'number' && displayValue !== fullPrecisionValue)) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {content}
          </TooltipTrigger>
          <TooltipContent>
            {tooltipContent || (
              <div className="text-sm">
                <p className="font-medium">Exact value</p>
                <p className="text-slate-300 tabular-nums">{fullPrecisionValue}</p>
              </div>
            )}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }
  
  return content;
}

// ============================================================================
// METRIC CARD ROW (for consistent grid layouts)
// ============================================================================

interface MetricCardRowProps {
  children: ReactNode;
  columns?: 2 | 3 | 4 | 5;
  className?: string;
}

export function MetricCardRow({ children, columns = 4, className }: MetricCardRowProps) {
  const gridClass = {
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5",
  }[columns];
  
  return (
    <div className={cn("grid gap-4", gridClass, className)}>
      {children}
    </div>
  );
}


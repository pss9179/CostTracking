"use client";

import { cn } from "@/lib/utils";
import { formatSmartCost, formatPercentChange, formatCompactNumber } from "@/lib/format";
import { TrendingUp, TrendingDown, Minus, DollarSign, Zap, Calendar } from "lucide-react";

interface KPICardsProps {
  todayCost: number;
  weekCost: number;
  monthCost: number;
  previousPeriodCost?: number;
  totalCalls: number;
  className?: string;
}

export function KPICards({
  todayCost,
  weekCost,
  monthCost,
  previousPeriodCost = 0,
  totalCalls,
  className,
}: KPICardsProps) {
  const change = formatPercentChange(todayCost, previousPeriodCost);
  
  return (
    <div className={cn("grid grid-cols-2 lg:grid-cols-4 gap-4", className)}>
      {/* Today - Primary KPI */}
      <div className="col-span-2 lg:col-span-1 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-5 text-white">
        <div className="flex items-center gap-2 mb-1">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">Today</span>
        </div>
        <div className="flex items-baseline gap-3">
          <span className="text-3xl font-bold tracking-tight">
            {formatSmartCost(todayCost)}
          </span>
          {previousPeriodCost > 0 && (
            <span className={cn(
              "flex items-center gap-1 text-sm font-medium",
              change.direction === 'up' ? 'text-rose-400' : 
              change.direction === 'down' ? 'text-emerald-400' : 
              'text-slate-400'
            )}>
              {change.direction === 'up' && <TrendingUp className="w-3.5 h-3.5" />}
              {change.direction === 'down' && <TrendingDown className="w-3.5 h-3.5" />}
              {change.direction === 'flat' && <Minus className="w-3.5 h-3.5" />}
              {change.formatted}
            </span>
          )}
        </div>
        <p className="text-xs text-slate-400 mt-2">vs yesterday</p>
      </div>
      
      {/* This Week */}
      <div className="bg-white border border-slate-200/60 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-1">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">This Week</span>
        </div>
        <span className="text-2xl font-semibold text-slate-900 tracking-tight">
          {formatSmartCost(weekCost)}
        </span>
      </div>
      
      {/* This Month */}
      <div className="bg-white border border-slate-200/60 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-1">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">This Month</span>
        </div>
        <span className="text-2xl font-semibold text-slate-900 tracking-tight">
          {formatSmartCost(monthCost)}
        </span>
      </div>
      
      {/* API Calls */}
      <div className="bg-white border border-slate-200/60 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">API Calls</span>
        </div>
        <span className="text-2xl font-semibold text-slate-900 tracking-tight">
          {formatCompactNumber(totalCalls)}
        </span>
      </div>
    </div>
  );
}


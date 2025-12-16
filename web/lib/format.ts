/**
 * Comprehensive formatting utilities for LLM cost tracking
 * 
 * Design principles:
 * - Max 2 significant figures for compactness
 * - Progressive precision on hover (via tooltip)
 * - Consistent patterns across all displays
 * - Stable color mapping by category name hash
 */

// ============================================================================
// CURRENCY FORMATTING
// ============================================================================

/**
 * Smart cost formatting with automatic scale detection
 * 
 * Scale bands:
 * - < $0.001 → micro dollars (45µ$)
 * - $0.001 - $0.99 → dollars with decimals ($0.0698)
 * - $1 - $999 → dollars ($12.34)
 * - $1k - $999k → thousands ($1.2k)
 * - $1M+ → millions ($3.4M)
 */
export function formatSmartCost(cost: number | null | undefined, options?: { 
  showSign?: boolean; 
  compact?: boolean;
  precision?: 'compact' | 'full';
}): string {
  if (cost === null || cost === undefined || isNaN(cost)) return "$0";
  if (cost === 0) return "$0";
  
  const isNegative = cost < 0;
  const absValue = Math.abs(cost);
  const sign = options?.showSign && !isNegative ? '+' : '';
  const negSign = isNegative ? '-' : '';
  const fullPrecision = options?.precision === 'full';
  
  // Micro dollars: < $0.001
  if (absValue < 0.001) {
    const microDollars = absValue * 1000000;
    if (fullPrecision) {
      return `${negSign}${sign}$${absValue.toFixed(6)}`;
    }
    if (microDollars < 1) {
      return `${negSign}${sign}${microDollars.toFixed(1)}µ$`;
    }
    return `${negSign}${sign}${Math.round(microDollars)}µ$`;
  }
  
  // Sub-dollar: $0.001 - $0.99
  if (absValue < 1) {
    if (fullPrecision) {
      return `${negSign}${sign}$${absValue.toFixed(6)}`;
    }
    // Show enough decimals to be meaningful
    if (absValue < 0.01) {
      return `${negSign}${sign}$${absValue.toFixed(4)}`;
    }
    return `${negSign}${sign}$${absValue.toFixed(3)}`;
  }
  
  // Regular dollars: $1 - $999
  if (absValue < 1000) {
    return `${negSign}${sign}$${absValue.toFixed(2)}`;
  }
  
  // Thousands: $1k - $999k
  if (absValue < 1000000) {
    const k = absValue / 1000;
    return `${negSign}${sign}$${k.toFixed(k < 10 ? 1 : 0)}k`;
  }
  
  // Millions: $1M+
  const m = absValue / 1000000;
  return `${negSign}${sign}$${m.toFixed(m < 10 ? 1 : 0)}M`;
}

/**
 * Currency format for axis labels (more compact)
 */
export function formatAxisCost(cost: number): string {
  if (cost === 0) return "$0";
  
  const absValue = Math.abs(cost);
  
  if (absValue < 0.001) {
    const micro = absValue * 1000000;
    return `${micro.toFixed(0)}µ$`;
  }
  
  if (absValue < 1) {
    const milli = absValue * 1000;
    if (milli < 1) {
      return `${milli.toFixed(1)}m$`;
    }
    return `${milli.toFixed(0)}m$`;
  }
  
  if (absValue < 1000) {
    return `$${absValue.toFixed(absValue < 10 ? 1 : 0)}`;
  }
  
  if (absValue < 1000000) {
    return `$${(absValue / 1000).toFixed(0)}k`;
  }
  
  return `$${(absValue / 1000000).toFixed(1)}M`;
}

// ============================================================================
// NUMBER FORMATTING
// ============================================================================

/**
 * Compact number formatting (counts, calls, etc.)
 */
export function formatCompactNumber(num: number | null | undefined): string {
  if (num === null || num === undefined || isNaN(num)) return "0";
  if (num < 1000) return num.toLocaleString();
  if (num < 1000000) return `${(num / 1000).toFixed(num < 10000 ? 1 : 0)}k`;
  return `${(num / 1000000).toFixed(1)}M`;
}

/**
 * Duration formatting
 * - < 1s: show ms (456ms)
 * - >= 1s: show seconds (3.45s)
 * - >= 60s: show minutes (2m 15s)
 */
export function formatDuration(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || isNaN(ms)) return "0ms";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.round((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

/**
 * Percentage formatting
 * - < 1%: show 1 decimal (0.4%)
 * - >= 1%: whole number (45%)
 */
export function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return "0%";
  if (value === 0) return "0%";
  if (Math.abs(value) < 1) return `${value.toFixed(1)}%`;
  return `${Math.round(value)}%`;
}

// ============================================================================
// CHANGE/DELTA FORMATTING
// ============================================================================

export interface PercentChange {
  value: number;
  formatted: string;
  direction: 'up' | 'down' | 'flat';
}

/**
 * Calculate and format percentage change between two values
 */
export function formatPercentChange(current: number, previous: number): PercentChange {
  if (previous === 0) {
    if (current === 0) return { value: 0, formatted: '0%', direction: 'flat' };
    return { value: 100, formatted: '+∞', direction: 'up' };
  }
  
  const change = ((current - previous) / previous) * 100;
  
  // Consider changes less than 1% as flat
  if (Math.abs(change) < 1) {
    return { value: change, formatted: '0%', direction: 'flat' };
  }
  
  const direction = change > 0 ? 'up' : 'down';
  const sign = change > 0 ? '+' : '';
  
  return {
    value: change,
    formatted: `${sign}${Math.round(change)}%`,
    direction
  };
}

// ============================================================================
// MODEL FAMILY GROUPING
// ============================================================================

/**
 * Get model family from model name for grouping
 */
export function getModelFamily(model: string): string {
  const lowerModel = model.toLowerCase();
  
  // GPT-4 variants
  if (lowerModel.includes('gpt-4o-mini')) return 'GPT-4o mini';
  if (lowerModel.includes('gpt-4o')) return 'GPT-4o';
  if (lowerModel.includes('gpt-4-turbo')) return 'GPT-4 Turbo';
  if (lowerModel.includes('gpt-4')) return 'GPT-4';
  
  // GPT-3.5
  if (lowerModel.includes('gpt-3.5')) return 'GPT-3.5';
  
  // Claude variants
  if (lowerModel.includes('claude-3-5-sonnet') || lowerModel.includes('claude-3.5-sonnet')) return 'Claude 3.5 Sonnet';
  if (lowerModel.includes('claude-3-5-haiku') || lowerModel.includes('claude-3.5-haiku')) return 'Claude 3.5 Haiku';
  if (lowerModel.includes('claude-3-opus')) return 'Claude 3 Opus';
  if (lowerModel.includes('claude-3-sonnet')) return 'Claude 3 Sonnet';
  if (lowerModel.includes('claude-3-haiku')) return 'Claude 3 Haiku';
  if (lowerModel.includes('claude-2')) return 'Claude 2';
  if (lowerModel.includes('claude')) return 'Claude';
  
  // Gemini
  if (lowerModel.includes('gemini-1.5-pro')) return 'Gemini 1.5 Pro';
  if (lowerModel.includes('gemini-1.5-flash')) return 'Gemini 1.5 Flash';
  if (lowerModel.includes('gemini-pro')) return 'Gemini Pro';
  if (lowerModel.includes('gemini-flash')) return 'Gemini Flash';
  if (lowerModel.includes('gemini')) return 'Gemini';
  
  // Mistral
  if (lowerModel.includes('mistral-large')) return 'Mistral Large';
  if (lowerModel.includes('mistral-medium')) return 'Mistral Medium';
  if (lowerModel.includes('mistral-small')) return 'Mistral Small';
  if (lowerModel.includes('mixtral')) return 'Mixtral';
  if (lowerModel.includes('mistral')) return 'Mistral';
  
  // Llama
  if (lowerModel.includes('llama-3.1')) return 'Llama 3.1';
  if (lowerModel.includes('llama-3')) return 'Llama 3';
  if (lowerModel.includes('llama-2')) return 'Llama 2';
  if (lowerModel.includes('llama')) return 'Llama';
  
  // Cohere
  if (lowerModel.includes('command-r-plus')) return 'Command R+';
  if (lowerModel.includes('command-r')) return 'Command R';
  if (lowerModel.includes('command')) return 'Command';
  
  // Default: capitalize
  return model.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

// ============================================================================
// STABLE COLOR MAPPING
// ============================================================================

/**
 * Hash a string to get a stable index
 * Uses djb2 hash algorithm for good distribution
 */
function hashString(str: string): number {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
  }
  return Math.abs(hash);
}

// Carefully curated color palette for data visualization
// Colors are distinguishable, accessible, and aesthetically pleasing
const DATA_COLORS = [
  '#10b981', // emerald-500
  '#8b5cf6', // violet-500
  '#3b82f6', // blue-500
  '#f59e0b', // amber-500
  '#ec4899', // pink-500
  '#06b6d4', // cyan-500
  '#84cc16', // lime-500
  '#f97316', // orange-500
  '#6366f1', // indigo-500
  '#14b8a6', // teal-500
  '#a855f7', // purple-500
  '#ef4444', // red-500
];

// Known provider colors (for consistency across the app)
const PROVIDER_COLOR_MAP: Record<string, string> = {
  openai: '#10b981',      // emerald
  anthropic: '#8b5cf6',   // violet
  cohere: '#6366f1',      // indigo
  google: '#3b82f6',      // blue
  mistral: '#ec4899',     // pink
  pinecone: '#f97316',    // orange
  stripe: '#a855f7',      // purple
  vapi: '#06b6d4',        // cyan
  elevenlabs: '#14b8a6',  // teal
  twilio: '#f59e0b',      // amber
  voyage: '#84cc16',      // lime
  deepgram: '#ef4444',    // red
  playht: '#a855f7',      // purple
  cartesia: '#6366f1',    // indigo
};

/**
 * Get a stable color for a category name
 * Same name always returns same color across sessions/pages
 */
export function getStableColor(name: string): string {
  const lowerName = name.toLowerCase();
  
  // Check known providers first
  if (PROVIDER_COLOR_MAP[lowerName]) {
    return PROVIDER_COLOR_MAP[lowerName];
  }
  
  // Hash for consistent color assignment
  const index = hashString(lowerName) % DATA_COLORS.length;
  return DATA_COLORS[index];
}

/**
 * Get colors for an array of categories
 * Ensures no adjacent duplicates where possible
 */
export function getCategoryColors(categories: string[]): Record<string, string> {
  const colors: Record<string, string> = {};
  const usedRecently: string[] = [];
  
  categories.forEach(cat => {
    const baseColor = getStableColor(cat);
    
    // Check if this color was used in the last 2 items
    if (usedRecently.includes(baseColor) && categories.length > 3) {
      // Find an alternative from the palette
      const altIndex = (DATA_COLORS.indexOf(baseColor) + 3) % DATA_COLORS.length;
      colors[cat] = DATA_COLORS[altIndex];
    } else {
      colors[cat] = baseColor;
    }
    
    usedRecently.push(colors[cat]);
    if (usedRecently.length > 2) usedRecently.shift();
  });
  
  return colors;
}

// ============================================================================
// TOP-N WITH "OTHER" AGGREGATION
// ============================================================================

export interface TopNItem<T> {
  item: T;
  isOther: boolean;
  otherItems?: T[];
  otherCount?: number;
}

export interface TopNResult<T> {
  items: TopNItem<T>[];
  topN: T[];
  other: T[];
  hasOther: boolean;
  otherTotal: number;
}

/**
 * Split an array into top N items + "Other" aggregate
 * Essential for scalable charts and tables
 */
export function getTopNWithOther<T>(
  items: T[],
  n: number,
  getValue: (item: T) => number,
  options?: {
    minOtherPercent?: number; // Minimum % for "Other" to show (default 0.5%)
    sortDesc?: boolean;       // Sort descending (default true)
  }
): TopNResult<T> {
  const { minOtherPercent = 0.5, sortDesc = true } = options || {};
  
  // Sort by value
  const sorted = [...items].sort((a, b) => 
    sortDesc ? getValue(b) - getValue(a) : getValue(a) - getValue(b)
  );
  
  const total = items.reduce((sum, item) => sum + getValue(item), 0);
  const topN = sorted.slice(0, n);
  const other = sorted.slice(n);
  const otherTotal = other.reduce((sum, item) => sum + getValue(item), 0);
  
  // Don't show "Other" if it's tiny
  const otherPercent = total > 0 ? (otherTotal / total) * 100 : 0;
  const showOther = other.length > 0 && otherPercent >= minOtherPercent;
  
  const result: TopNItem<T>[] = topN.map(item => ({
    item,
    isOther: false,
  }));
  
  if (showOther && other.length > 0) {
    result.push({
      item: other[0], // Placeholder, won't be used directly
      isOther: true,
      otherItems: other,
      otherCount: other.length,
    });
  }
  
  return {
    items: result,
    topN,
    other: showOther ? other : [],
    hasOther: showOther,
    otherTotal: showOther ? otherTotal : 0,
  };
}

// ============================================================================
// FEATURE/SECTION PARSING
// ============================================================================

export interface ParsedFeature {
  type: 'feature' | 'agent' | 'step' | 'tool' | 'section';
  name: string;
  displayName: string;
  fullPath: string;
}

/**
 * Parse a section/feature string into structured data
 */
export function parseFeatureSection(section: string): ParsedFeature {
  const fullPath = section;
  
  // Handle prefixed sections
  if (section.startsWith('feature:')) {
    const name = section.replace('feature:', '');
    return {
      type: 'feature',
      name,
      displayName: formatDisplayName(name),
      fullPath,
    };
  }
  if (section.startsWith('agent:')) {
    const name = section.replace('agent:', '');
    return {
      type: 'agent',
      name,
      displayName: formatDisplayName(name),
      fullPath,
    };
  }
  if (section.startsWith('step:')) {
    const name = section.replace('step:', '');
    return {
      type: 'step',
      name,
      displayName: formatDisplayName(name),
      fullPath,
    };
  }
  if (section.startsWith('tool:')) {
    const name = section.replace('tool:', '');
    return {
      type: 'tool',
      name,
      displayName: formatDisplayName(name),
      fullPath,
    };
  }
  
  // Plain section
  return {
    type: 'section',
    name: section,
    displayName: formatDisplayName(section),
    fullPath,
  };
}

/**
 * Convert snake_case or kebab-case to Title Case
 */
function formatDisplayName(name: string): string {
  return name
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Get badge color class for feature type
 */
export function getFeatureTypeColor(type: ParsedFeature['type']): string {
  switch (type) {
    case 'feature': return 'bg-emerald-100 text-emerald-700';
    case 'agent': return 'bg-violet-100 text-violet-700';
    case 'step': return 'bg-blue-100 text-blue-700';
    case 'tool': return 'bg-amber-100 text-amber-700';
    default: return 'bg-slate-100 text-slate-700';
  }
}

// ============================================================================
// DATE/TIME UTILITIES
// ============================================================================

/**
 * Format date for display
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format date with time
 */
export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

/**
 * Get relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  
  return formatDate(d);
}

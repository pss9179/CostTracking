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
 * Groups models into broad families for cleaner dashboard display
 */
export function getModelFamily(model: string): string {
  const lowerModel = model.toLowerCase();
  
  // OpenAI GPT family (all GPT models grouped together)
  if (lowerModel.includes('gpt-5')) return 'GPT-5';
  if (lowerModel.includes('gpt-4')) return 'GPT-4';
  if (lowerModel.includes('gpt-3')) return 'GPT-3.5';
  if (lowerModel.includes('o1') || lowerModel.includes('o3') || lowerModel.includes('o4')) return 'OpenAI o-series';
  
  // Anthropic Claude family (all Claude models grouped together)
  if (lowerModel.includes('claude-opus')) return 'Claude Opus';
  if (lowerModel.includes('claude-sonnet')) return 'Claude Sonnet';
  if (lowerModel.includes('claude') && lowerModel.includes('haiku')) return 'Claude Haiku';
  if (lowerModel.includes('claude-3.5') || lowerModel.includes('claude-3-5')) return 'Claude 3.5';
  if (lowerModel.includes('claude-3')) return 'Claude 3';
  if (lowerModel.includes('claude')) return 'Claude';
  
  // xAI Grok family (all Grok models grouped together)
  if (lowerModel.includes('grok')) return 'Grok';
  
  // Google Gemini family
  if (lowerModel.includes('gemini')) return 'Gemini';
  
  // Mistral family (includes Mixtral, Codestral)
  if (lowerModel.includes('mixtral') || lowerModel.includes('mistral') || lowerModel.includes('codestral')) return 'Mistral';
  
  // Meta Llama family
  if (lowerModel.includes('llama')) return 'Llama';
  
  // DeepSeek family
  if (lowerModel.includes('deepseek')) return 'DeepSeek';
  
  // Qwen family
  if (lowerModel.includes('qwen')) return 'Qwen';
  
  // Cohere family
  if (lowerModel.includes('command')) return 'Cohere';
  
  // Amazon Nova family
  if (lowerModel.includes('nova')) return 'Nova';
  
  // Perplexity family
  if (lowerModel.includes('sonar') || lowerModel.includes('pplx')) return 'Perplexity';
  
  // Microsoft family
  if (lowerModel.includes('phi')) return 'Phi';
  
  // Default: capitalize first word
  const firstWord = model.split('-')[0];
  return firstWord.charAt(0).toUpperCase() + firstWord.slice(1);
}

// ============================================================================
// SEMANTIC COLOR SYSTEM
// ============================================================================

/**
 * Semantic color system for LLM cost observability dashboards
 * 
 * Design principles:
 * - Cost metrics use neutral blue (trustworthy, professional)
 * - Latency metrics use amber (warning, attention)
 * - Errors use red (alerts, problems)
 * - Providers use a muted categorical palette (distinguishable but not loud)
 * - Bright/saturated colors reserved for alerts only
 */

export const SEMANTIC_COLORS = {
  // Primary metrics
  cost: {
    primary: '#3b82f6',       // blue-500 - main cost visualization
    light: '#93c5fd',         // blue-300 - backgrounds, fills
    dark: '#1d4ed8',          // blue-700 - emphasis, selected
    muted: '#60a5fa',         // blue-400 - secondary
    bg: '#eff6ff',            // blue-50 - backgrounds
    bgHover: '#dbeafe',       // blue-100 - hover states
  },
  latency: {
    primary: '#f59e0b',       // amber-500 - main latency visualization
    light: '#fcd34d',         // amber-300 - backgrounds
    dark: '#d97706',          // amber-600 - emphasis
    muted: '#fbbf24',         // amber-400 - secondary
    bg: '#fffbeb',            // amber-50 - backgrounds
    bgHover: '#fef3c7',       // amber-100 - hover
  },
  error: {
    primary: '#ef4444',       // red-500 - errors, failures
    light: '#fca5a5',         // red-300 - backgrounds
    dark: '#dc2626',          // red-600 - emphasis
    muted: '#f87171',         // red-400 - secondary
    bg: '#fef2f2',            // red-50 - backgrounds
    bgHover: '#fee2e2',       // red-100 - hover
  },
  success: {
    primary: '#10b981',       // emerald-500 - success, positive
    light: '#6ee7b7',         // emerald-300 - backgrounds
    dark: '#059669',          // emerald-600 - emphasis
    muted: '#34d399',         // emerald-400 - secondary
    bg: '#ecfdf5',            // emerald-50 - backgrounds
    bgHover: '#d1fae5',       // emerald-100 - hover
  },
  neutral: {
    primary: '#64748b',       // slate-500 - neutral, secondary info
    light: '#cbd5e1',         // slate-300 - borders
    dark: '#475569',          // slate-600 - text
    muted: '#94a3b8',         // slate-400 - muted text
    bg: '#f8fafc',            // slate-50 - backgrounds
    bgHover: '#f1f5f9',       // slate-100 - hover
  },
} as const;

/**
 * Alert severity colors (bright, saturated - use sparingly)
 */
export const ALERT_COLORS = {
  critical: '#dc2626',        // red-600 - exceeded limits
  warning: '#d97706',         // amber-600 - approaching limits
  info: '#2563eb',            // blue-600 - informational
  success: '#059669',         // emerald-600 - resolved
} as const;

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

/**
 * Provider color palette - muted categorical colors
 * Consistent across all visualizations
 * Colors are intentionally muted (not saturated) for professional look
 */
export const PROVIDER_COLORS: Record<string, string> = {
  // LLM Providers
  openai: '#059669',          // emerald-600 (primary, most common)
  anthropic: '#7c3aed',       // violet-600
  google: '#2563eb',          // blue-600
  cohere: '#4f46e5',          // indigo-600
  mistral: '#db2777',         // pink-600
  groq: '#ca8a04',            // yellow-600
  perplexity: '#0891b2',      // cyan-600
  together: '#ea580c',        // orange-600
  replicate: '#9333ea',       // purple-600
  huggingface: '#eab308',     // yellow-500
  azure: '#0284c7',           // sky-600
  aws: '#f97316',             // orange-500
  fireworks: '#c026d3',       // fuchsia-600
  anyscale: '#4ade80',        // green-400
  
  // Voice Providers
  vapi: '#0d9488',            // teal-600
  elevenlabs: '#14b8a6',      // teal-500
  deepgram: '#0ea5e9',        // sky-500
  twilio: '#dc2626',          // red-600
  cartesia: '#8b5cf6',        // violet-500
  playht: '#ec4899',          // pink-500
  assembly: '#6366f1',        // indigo-500
  
  // Utility Providers
  pinecone: '#f97316',        // orange-500
  stripe: '#6366f1',          // indigo-500
  voyage: '#84cc16',          // lime-500
  weaviate: '#10b981',        // emerald-500
  chroma: '#f59e0b',          // amber-500
  
  // Internal/Other
  internal: '#94a3b8',        // slate-400
  unknown: '#64748b',         // slate-500
  other: '#94a3b8',           // slate-400
};

// Alias for backward compatibility
const PROVIDER_COLOR_MAP = PROVIDER_COLORS;

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
 * Get provider-specific color
 */
export function getProviderColor(provider: string): string {
  return PROVIDER_COLORS[provider.toLowerCase()] || PROVIDER_COLORS.other;
}

/**
 * Get semantic color for a metric type
 */
export function getMetricColor(
  type: 'cost' | 'latency' | 'error' | 'success' | 'neutral',
  variant: 'primary' | 'light' | 'dark' | 'muted' | 'bg' | 'bgHover' = 'primary'
): string {
  return SEMANTIC_COLORS[type][variant];
}

/**
 * Get color class for Tailwind (background + text)
 */
export function getMetricColorClass(
  type: 'cost' | 'latency' | 'error' | 'success' | 'neutral'
): { bg: string; text: string; border: string } {
  switch (type) {
    case 'cost':
      return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' };
    case 'latency':
      return { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' };
    case 'error':
      return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' };
    case 'success':
      return { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' };
    default:
      return { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200' };
  }
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

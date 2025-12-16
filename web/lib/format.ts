/**
 * Smart cost formatting utility
 * 
 * Rules:
 * - Max 2 significant figures
 * - < $0.001 → micro dollars (µ$29)
 * - $0.001 - $0.99 → milli dollars (m$1.04)
 * - $1 - $999 → dollars ($1.23)
 * - $1k+ → abbreviated ($1.2k, $5.4M)
 */

export function formatSmartCost(cost: number, options?: { 
  showSign?: boolean; 
  compact?: boolean;
}): string {
  if (cost === null || cost === undefined || isNaN(cost)) return "$0";
  if (cost === 0) return "$0";
  
  const isNegative = cost < 0;
  const absValue = Math.abs(cost);
  const sign = options?.showSign && !isNegative ? '+' : '';
  const negSign = isNegative ? '-' : '';
  
  // Micro dollars: < $0.001 (< 1 milli)
  if (absValue < 0.001) {
    const microDollars = absValue * 1000000;
    if (microDollars < 1) {
      return `${negSign}${sign}${microDollars.toFixed(1)}µ$`;
    }
    return `${negSign}${sign}${Math.round(microDollars)}µ$`;
  }
  
  // Milli dollars: $0.001 - $0.99
  if (absValue < 1) {
    if (options?.compact) {
      const milliDollars = absValue * 1000;
      return `${negSign}${sign}${milliDollars.toFixed(1)}m$`;
    }
    // Show as regular dollars with appropriate precision
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
 * Format cost for Y-axis labels
 */
export function formatAxisCost(cost: number): string {
  if (cost === 0) return "$0";
  
  const absValue = Math.abs(cost);
  
  // Micro range
  if (absValue < 0.001) {
    const micro = absValue * 1000000;
    return `${micro.toFixed(0)}µ$`;
  }
  
  // Milli range
  if (absValue < 1) {
    const milli = absValue * 1000;
    if (milli < 1) {
      return `${milli.toFixed(1)}m$`;
    }
    return `${milli.toFixed(0)}m$`;
  }
  
  // Dollar range
  if (absValue < 1000) {
    return `$${absValue.toFixed(absValue < 10 ? 1 : 0)}`;
  }
  
  // K range
  if (absValue < 1000000) {
    return `$${(absValue / 1000).toFixed(0)}k`;
  }
  
  // M range
  return `$${(absValue / 1000000).toFixed(1)}M`;
}

/**
 * Calculate percentage change
 */
export function formatPercentChange(current: number, previous: number): { 
  value: number; 
  formatted: string; 
  direction: 'up' | 'down' | 'flat';
} {
  if (previous === 0) {
    if (current === 0) return { value: 0, formatted: '0%', direction: 'flat' };
    return { value: 100, formatted: '+100%', direction: 'up' };
  }
  
  const change = ((current - previous) / previous) * 100;
  const direction = change > 1 ? 'up' : change < -1 ? 'down' : 'flat';
  const sign = change > 0 ? '+' : '';
  
  return {
    value: change,
    formatted: `${sign}${change.toFixed(0)}%`,
    direction
  };
}

/**
 * Format number with abbreviation
 */
export function formatCompactNumber(num: number): string {
  if (num < 1000) return num.toString();
  if (num < 1000000) return `${(num / 1000).toFixed(num < 10000 ? 1 : 0)}k`;
  return `${(num / 1000000).toFixed(1)}M`;
}

/**
 * Get model family from model name
 * Groups models by family (e.g., gpt-4, gpt-4o, gpt-4-turbo → "GPT-4")
 */
export function getModelFamily(model: string): string {
  const lowerModel = model.toLowerCase();
  
  // GPT-4 variants
  if (lowerModel.includes('gpt-4o')) return 'GPT-4o';
  if (lowerModel.includes('gpt-4-turbo')) return 'GPT-4 Turbo';
  if (lowerModel.includes('gpt-4')) return 'GPT-4';
  
  // GPT-3.5
  if (lowerModel.includes('gpt-3.5')) return 'GPT-3.5';
  
  // Claude variants
  if (lowerModel.includes('claude-3-opus')) return 'Claude 3 Opus';
  if (lowerModel.includes('claude-3-sonnet')) return 'Claude 3 Sonnet';
  if (lowerModel.includes('claude-3-haiku')) return 'Claude 3 Haiku';
  if (lowerModel.includes('claude-3.5-sonnet') || lowerModel.includes('claude-3-5-sonnet')) return 'Claude 3.5 Sonnet';
  if (lowerModel.includes('claude-3.5-haiku') || lowerModel.includes('claude-3-5-haiku')) return 'Claude 3.5 Haiku';
  if (lowerModel.includes('claude-2')) return 'Claude 2';
  if (lowerModel.includes('claude')) return 'Claude';
  
  // Gemini
  if (lowerModel.includes('gemini-pro')) return 'Gemini Pro';
  if (lowerModel.includes('gemini-flash')) return 'Gemini Flash';
  if (lowerModel.includes('gemini')) return 'Gemini';
  
  // Mistral
  if (lowerModel.includes('mistral-large')) return 'Mistral Large';
  if (lowerModel.includes('mistral-medium')) return 'Mistral Medium';
  if (lowerModel.includes('mistral-small')) return 'Mistral Small';
  if (lowerModel.includes('mistral')) return 'Mistral';
  
  // Llama
  if (lowerModel.includes('llama-3')) return 'Llama 3';
  if (lowerModel.includes('llama-2')) return 'Llama 2';
  if (lowerModel.includes('llama')) return 'Llama';
  
  // Default: capitalize first letter of each word
  return model.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}


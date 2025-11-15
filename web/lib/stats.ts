/**
 * Format cost in USD
 */
export function formatCost(cost: number): string {
  // Handle null/undefined
  if (cost === null || cost === undefined || isNaN(cost)) return "$0.00";
  
  // Handle zero
  if (cost === 0) return "$0.00";
  
  // For very small costs (micro-costs), show scientific notation or more precision
  if (cost < 0.000001 && cost > 0) {
    // Show up to 10 decimals, but strip trailing zeros
    const formatted = cost.toFixed(10).replace(/\.?0+$/, '');
    return `$${formatted}`;
  }
  
  if (cost < 0.01) return `$${cost.toFixed(6)}`;
  if (cost < 1) return `$${cost.toFixed(4)}`;
  if (cost < 100) return `$${cost.toFixed(2)}`;
  return `$${cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Format duration in milliseconds to human-readable string
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

/**
 * Format token count
 */
export function formatTokens(tokens: number | null | undefined): string {
  if (tokens === null || tokens === undefined) return "N/A";
  if (tokens < 1000) return tokens.toString();
  if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}K`;
  return `${(tokens / 1000000).toFixed(2)}M`;
}

/**
 * Calculate percentage
 */
export function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0;
  return (value / total) * 100;
}


import type { RunDetail } from "./api";

export interface AggregatedByProvider {
  provider: string;
  cost: number;
  calls: number;
  percentage: number;
}

export interface AggregatedByModel {
  model: string;
  cost: number;
  calls: number;
  percentage: number;
}

export interface AggregatedByAgent {
  agent: string;
  cost: number;
  calls: number;
  percentage: number;
}

export interface AggregatedByDay {
  date: string;
  cost: number;
  calls: number;
}

/**
 * Aggregate events by provider
 * Accepts either RunDetail[] (with events property) or Event[] directly
 */
export function aggregateByProvider(runDetailsOrEvents: RunDetail[] | any[]): AggregatedByProvider[] {
  const providerMap = new Map<string, { cost: number; calls: number }>();

  // Check if first item has 'events' property (RunDetail) or is an event itself
  const events = runDetailsOrEvents.length > 0 && runDetailsOrEvents[0]?.events
    ? runDetailsOrEvents.flatMap((run: RunDetail) => run.events || [])
    : runDetailsOrEvents;

  events.forEach((event: any) => {
    if (!event) return; // Skip null/undefined events
    const provider = event.provider || "unknown";
    const existing = providerMap.get(provider) || { cost: 0, calls: 0 };
    existing.cost += event.cost_usd || 0;
    existing.calls += 1;
    providerMap.set(provider, existing);
  });

  const totalCost = Array.from(providerMap.values()).reduce((sum, p) => sum + p.cost, 0);

  return Array.from(providerMap.entries())
    .map(([provider, stats]) => ({
      provider,
      cost: stats.cost,
      calls: stats.calls,
      percentage: totalCost > 0 ? (stats.cost / totalCost) * 100 : 0,
    }))
    .sort((a, b) => b.cost - a.cost);
}

/**
 * Aggregate events by model
 * Accepts either RunDetail[] (with events property) or Event[] directly
 */
export function aggregateByModel(runDetailsOrEvents: RunDetail[] | any[]): AggregatedByModel[] {
  const modelMap = new Map<string, { cost: number; calls: number }>();

  // Check if first item has 'events' property (RunDetail) or is an event itself
  const events = runDetailsOrEvents.length > 0 && runDetailsOrEvents[0]?.events
    ? runDetailsOrEvents.flatMap((run: RunDetail) => run.events || [])
    : runDetailsOrEvents;

  events.forEach((event: any) => {
    if (!event) return; // Skip null/undefined events
    const model = event.model || "unknown";
    const existing = modelMap.get(model) || { cost: 0, calls: 0 };
    existing.cost += event.cost_usd || 0;
    existing.calls += 1;
    modelMap.set(model, existing);
  });

  const totalCost = Array.from(modelMap.values()).reduce((sum, m) => sum + m.cost, 0);

  return Array.from(modelMap.entries())
    .map(([model, stats]) => ({
      model,
      cost: stats.cost,
      calls: stats.calls,
      percentage: totalCost > 0 ? (stats.cost / totalCost) * 100 : 0,
    }))
    .sort((a, b) => b.cost - a.cost);
}

/**
 * Aggregate events by agent (section starting with "agent:")
 * Accepts either RunDetail[] (with events property) or Event[] directly
 */
export function aggregateByAgent(runDetailsOrEvents: RunDetail[] | any[]): AggregatedByAgent[] {
  const agentMap = new Map<string, { cost: number; calls: number }>();

  // Check if first item has 'events' property (RunDetail) or is an event itself
  const events = runDetailsOrEvents.length > 0 && runDetailsOrEvents[0]?.events
    ? runDetailsOrEvents.flatMap((run: RunDetail) => run.events || [])
    : runDetailsOrEvents;

  events.forEach((event: any) => {
    if (!event) return; // Skip null/undefined events
    const section = event.section_path || event.section || "";
    if (!section.startsWith("agent:")) return;

    const agent = section.split("/")[0] || section;
    const existing = agentMap.get(agent) || { cost: 0, calls: 0 };
    existing.cost += event.cost_usd || 0;
    existing.calls += 1;
    agentMap.set(agent, existing);
  });

  const totalCost = Array.from(agentMap.values()).reduce((sum, a) => sum + a.cost, 0);

  return Array.from(agentMap.entries())
    .map(([agent, stats]) => ({
      agent,
      cost: stats.cost,
      calls: stats.calls,
      percentage: totalCost > 0 ? (stats.cost / totalCost) * 100 : 0,
    }))
    .sort((a, b) => b.cost - a.cost);
}

/**
 * Aggregate events by day
 * Accepts either RunDetail[] (with events property) or Event[] directly
 */
export function aggregateByDay(runDetailsOrEvents: RunDetail[] | any[]): AggregatedByDay[] {
  const dayMap = new Map<string, { cost: number; calls: number }>();

  // Check if first item has 'events' property (RunDetail) or is an event itself
  const events = runDetailsOrEvents.length > 0 && runDetailsOrEvents[0]?.events
    ? runDetailsOrEvents.flatMap((run: RunDetail) => run.events || [])
    : runDetailsOrEvents;

  events.forEach((event: any) => {
    if (!event || !event.created_at) return; // Skip null/undefined events or events without created_at
    const date = new Date(event.created_at).toISOString().split("T")[0];
    const existing = dayMap.get(date) || { cost: 0, calls: 0 };
    existing.cost += event.cost_usd || 0;
    existing.calls += 1;
    dayMap.set(date, existing);
  });

  return Array.from(dayMap.entries())
    .map(([date, stats]) => ({
      date,
      cost: stats.cost,
      calls: stats.calls,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
}


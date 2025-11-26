/**
 * Context management for tracking tenant, customer, and agent information
 */

interface Context {
  tenantId: string;
  customerId: string;
  agentStack: string[];
  runId: string;
}

let _context: Context = {
  tenantId: 'default_tenant',
  customerId: '',
  agentStack: [],
  runId: '',
};

export function getContext(): Context {
  return { ..._context };
}

export function setContext(ctx: Context): void {
  _context = { ...ctx };
}

export function getCurrentAgent(): string | null {
  if (_context.agentStack.length === 0) return null;
  return _context.agentStack[_context.agentStack.length - 1];
}


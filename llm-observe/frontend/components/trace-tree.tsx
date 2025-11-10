"use client";

import { useState } from "react";
import { CostEvent } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  ChevronRight, 
  ChevronDown, 
  Zap, 
  Clock, 
  DollarSign, 
  Database, 
  MessageSquare, 
  Calendar, 
  Mail, 
  Phone,
  Bot,
  Wrench,
  Activity,
  TrendingUp,
  FileText
} from "lucide-react";
import { cn } from "@/lib/utils";

interface TreeNode {
  id: string;
  name: string;
  type: "workflow" | "agent" | "step" | "tool_call" | "llm_call" | "summary" | "api_call";
  provider?: string;
  cost?: number;
  duration?: number;
  timestamp?: string;
  children?: TreeNode[];
  metadata?: Record<string, any>;
  level?: number;
}

interface TraceTreeProps {
  events: CostEvent[];
}

const providerIcons: Record<string, any> = {
  openai: MessageSquare,
  pinecone: Database,
  google: Calendar,
  vapi: Phone,
  gmail: Mail,
  tool: Wrench,
  langchain_tool: Wrench,
};

const providerColors: Record<string, string> = {
  openai: "bg-green-500",
  pinecone: "bg-purple-500",
  google: "bg-blue-500",
  vapi: "bg-orange-500",
  gmail: "bg-red-500",
  tool: "bg-indigo-500",
  langchain_tool: "bg-indigo-500",
};

const typeColors: Record<string, string> = {
  workflow: "bg-blue-600",
  agent: "bg-purple-600",
  step: "bg-cyan-600",
  tool_call: "bg-indigo-600",
  llm_call: "bg-green-600",
  summary: "bg-amber-600",
  api_call: "bg-gray-600",
};

function buildTree(events: CostEvent[]): TreeNode[] {
  // Group events by workflow_id and trace_id
  const workflows = new Map<string, Map<string, CostEvent[]>>();
  
  events.forEach(event => {
    const workflowId = event.workflow_id || "orphaned";
    const traceId = event.trace_id || "no-trace";
    
    if (!workflows.has(workflowId)) {
      workflows.set(workflowId, new Map());
    }
    
    const traces = workflows.get(workflowId)!;
    if (!traces.has(traceId)) {
      traces.set(traceId, []);
    }
    
    traces.get(traceId)!.push(event);
  });

  const tree: TreeNode[] = [];

  workflows.forEach((traces, workflowId) => {
    traces.forEach((traceEvents, traceId) => {
      // Sort events by timestamp
      traceEvents.sort((a, b) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );

      // Group events into logical steps based on timing and operation types
      // Steps are clusters of events that happen close together
      const STEP_THRESHOLD_MS = 2000; // Events within 2 seconds are in the same step
      const steps: CostEvent[][] = [];
      let currentStep: CostEvent[] = [];
      let lastTimestamp = 0;

      traceEvents.forEach((event, idx) => {
        const eventTime = new Date(event.timestamp).getTime();
        
        if (idx === 0 || eventTime - lastTimestamp > STEP_THRESHOLD_MS) {
          // Start new step
          if (currentStep.length > 0) {
            steps.push(currentStep);
          }
          currentStep = [event];
        } else {
          // Add to current step
          currentStep.push(event);
        }
        
        lastTimestamp = eventTime;
      });
      
      if (currentStep.length > 0) {
        steps.push(currentStep);
      }

      // Build hierarchical structure
      const workflowNode: TreeNode = {
        id: `workflow-${workflowId}-${traceId}`,
        name: workflowId === "orphaned" ? "Orphaned Events" : `Workflow: ${workflowId}`,
        type: "workflow",
        cost: traceEvents.reduce((sum, e) => sum + e.cost_usd, 0),
        duration: traceEvents.reduce((sum, e) => sum + e.duration_ms, 0),
        timestamp: traceEvents[0]?.timestamp,
        children: [],
        metadata: { workflow_id: workflowId, trace_id: traceId },
      };

      // Create agent node (inferred from workflow)
      const agentName = workflowId.includes("customer-support") 
        ? "CustomerSupportAgent"
        : workflowId.includes("calendar") || workflowId.includes("email")
        ? "CalendarEmailAssistant"
        : "Agent";
      
      const agentNode: TreeNode = {
        id: `agent-${workflowId}-${traceId}`,
        name: `Agent: ${agentName}`,
        type: "agent",
        cost: traceEvents.reduce((sum, e) => sum + e.cost_usd, 0),
        duration: traceEvents.reduce((sum, e) => sum + e.duration_ms, 0),
        timestamp: traceEvents[0]?.timestamp,
        children: [],
        metadata: { agent_name: agentName },
      };

      // Create step nodes
      steps.forEach((stepEvents, stepIdx) => {
        const stepNode: TreeNode = {
          id: `step-${workflowId}-${traceId}-${stepIdx}`,
          name: `Step ${stepIdx + 1}`,
          type: "step",
          cost: stepEvents.reduce((sum, e) => sum + e.cost_usd, 0),
          duration: stepEvents.reduce((sum, e) => sum + e.duration_ms, 0),
          timestamp: stepEvents[0]?.timestamp,
          children: [],
          metadata: { step_number: stepIdx + 1 },
        };

        // Group step events by type
        stepEvents.forEach((event) => {
          if (event.operation === "tool" || event.provider === "tool" || event.provider === "langchain_tool") {
            // Tool call
            const toolNode: TreeNode = {
              id: `tool-${event.id}`,
              name: `ToolCall: ${event.model || event.operation || "unknown"}`,
              type: "tool_call",
              provider: event.provider,
              cost: event.cost_usd,
              duration: event.duration_ms,
              timestamp: event.timestamp,
              metadata: {
                model: event.model,
                operation: event.operation,
                tokens: event.total_tokens,
              },
            };
            stepNode.children!.push(toolNode);
          } else if (event.operation === "llm" || event.provider === "openai" || event.model) {
            // LLM call
            const llmNode: TreeNode = {
              id: `llm-${event.id}`,
              name: `${event.provider} - ${event.model || event.operation || "llm"}`,
              type: "llm_call",
              provider: event.provider,
              cost: event.cost_usd,
              duration: event.duration_ms,
              timestamp: event.timestamp,
              metadata: {
                model: event.model,
                tokens: event.total_tokens,
                prompt_tokens: event.prompt_tokens,
                completion_tokens: event.completion_tokens,
                operation: event.operation,
              },
            };
            stepNode.children!.push(llmNode);
          } else {
            // Generic API call
            const apiNode: TreeNode = {
              id: `api-${event.id}`,
              name: `${event.provider} - ${event.operation || "api_call"}`,
              type: "api_call",
              provider: event.provider,
              cost: event.cost_usd,
              duration: event.duration_ms,
              timestamp: event.timestamp,
              metadata: {
                model: event.model,
                tokens: event.total_tokens,
                operation: event.operation,
              },
            };
            stepNode.children!.push(apiNode);
          }
        });

        agentNode.children!.push(stepNode);
      });

      // Add AgentSummary node
      const summaryNode: TreeNode = {
        id: `summary-${workflowId}-${traceId}`,
        name: "AgentSummary",
        type: "summary",
        cost: traceEvents.reduce((sum, e) => sum + e.cost_usd, 0),
        duration: traceEvents.reduce((sum, e) => sum + e.duration_ms, 0),
        timestamp: traceEvents[traceEvents.length - 1]?.timestamp,
        metadata: {
          total_cost: traceEvents.reduce((sum, e) => sum + e.cost_usd, 0),
          total_duration: traceEvents.reduce((sum, e) => sum + e.duration_ms, 0),
          llm_call_count: traceEvents.filter(e => e.operation === "llm" || e.provider === "openai").length,
          tool_call_count: traceEvents.filter(e => e.operation === "tool" || e.provider === "tool" || e.provider === "langchain_tool").length,
          step_count: steps.length,
        },
      };
      
      agentNode.children!.push(summaryNode);
      workflowNode.children!.push(agentNode);
      tree.push(workflowNode);
    });
  });

  return tree;
}

function TreeNodeComponent({ 
  node, 
  level = 0, 
  expanded, 
  onToggle 
}: { 
  node: TreeNode; 
  level: number; 
  expanded: Set<string>; 
  onToggle: (id: string) => void;
}) {
  const isExpanded = expanded.has(node.id);
  const hasChildren = node.children && node.children.length > 0;
  
  // Choose icon based on type
  let Icon = Zap;
  if (node.type === "agent") Icon = Bot;
  else if (node.type === "step") Icon = Activity;
  else if (node.type === "tool_call") Icon = Wrench;
  else if (node.type === "llm_call") Icon = MessageSquare;
  else if (node.type === "summary") Icon = TrendingUp;
  else if (node.type === "workflow") Icon = FileText;
  else if (node.provider) Icon = providerIcons[node.provider] || Zap;
  
  // Choose color based on type or provider
  const bgColor = node.type && typeColors[node.type] 
    ? typeColors[node.type] 
    : node.provider && providerColors[node.provider]
    ? providerColors[node.provider]
    : "bg-gray-500";

  const indentLevel = level * 1.5;

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 py-2.5 px-3 rounded-lg transition-all",
          "hover:bg-accent/50 cursor-pointer border border-transparent hover:border-border",
          level === 0 && "bg-muted/30",
          level === 1 && "bg-muted/20",
        )}
        style={{ marginLeft: `${indentLevel}rem` }}
        onClick={() => hasChildren && onToggle(node.id)}
      >
        {hasChildren && (
          <Button
            variant="ghost"
            size="sm"
            className="h-5 w-5 p-0"
            onClick={(e) => {
              e.stopPropagation();
              onToggle(node.id);
            }}
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
        )}
        {!hasChildren && <div className="w-5" />}
        
        <div className={cn("p-1.5 rounded", bgColor)}>
          <Icon className="h-3.5 w-3.5 text-white" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={cn(
              "font-medium text-sm truncate",
              node.type === "workflow" && "text-base font-semibold",
              node.type === "agent" && "text-sm font-semibold text-purple-700 dark:text-purple-300",
              node.type === "step" && "text-sm font-medium text-cyan-700 dark:text-cyan-300",
              node.type === "summary" && "text-sm font-semibold text-amber-700 dark:text-amber-300",
            )}>
              {node.name}
            </span>
            {node.type === "workflow" && (
              <Badge variant="outline" className="text-xs">
                {node.children?.length || 0} agents
              </Badge>
            )}
            {node.type === "agent" && (
              <Badge variant="outline" className="text-xs bg-purple-100 dark:bg-purple-900">
                {node.children?.filter(c => c.type === "step").length || 0} steps
              </Badge>
            )}
            {node.type === "step" && (
              <Badge variant="outline" className="text-xs bg-cyan-100 dark:bg-cyan-900">
                {node.children?.length || 0} calls
              </Badge>
            )}
            {node.type === "summary" && node.metadata && (
              <div className="flex gap-2 text-xs">
                <Badge variant="outline" className="bg-amber-100 dark:bg-amber-900">
                  {node.metadata.llm_call_count || 0} LLM
                </Badge>
                <Badge variant="outline" className="bg-amber-100 dark:bg-amber-900">
                  {node.metadata.tool_call_count || 0} Tools
                </Badge>
                <Badge variant="outline" className="bg-amber-100 dark:bg-amber-900">
                  {node.metadata.step_count || 0} Steps
                </Badge>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground flex-wrap">
            {node.cost !== undefined && node.cost > 0 && (
              <span className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                ${node.cost.toFixed(4)}
              </span>
            )}
            {node.duration !== undefined && node.duration > 0 && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {node.duration.toFixed(0)}ms
              </span>
            )}
            {node.timestamp && (
              <span>{new Date(node.timestamp).toLocaleTimeString()}</span>
            )}
            {node.metadata?.tokens && (
              <span className="text-muted-foreground">
                {node.metadata.tokens.toLocaleString()} tokens
              </span>
            )}
          </div>
        </div>
      </div>

      {isExpanded && hasChildren && (
        <div className={cn(
          "border-l-2 ml-6 mt-1",
          level === 0 ? "border-blue-300 dark:border-blue-700" :
          level === 1 ? "border-purple-300 dark:border-purple-700" :
          "border-border"
        )}>
          {node.children!.map((child) => (
            <TreeNodeComponent
              key={child.id}
              node={child}
              level={level + 1}
              expanded={expanded}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function TraceTree({ events }: TraceTreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  
  const tree = buildTree(events);

  const toggleNode = (id: string) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpanded(newExpanded);
  };

  const expandAll = () => {
    const allIds = new Set<string>();
    const collectIds = (nodes: TreeNode[]) => {
      nodes.forEach(node => {
        if (node.children) {
          allIds.add(node.id);
          collectIds(node.children);
        }
      });
    };
    collectIds(tree);
    setExpanded(allIds);
  };

  const collapseAll = () => {
    setExpanded(new Set());
  };

  if (tree.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          No trace data available. Run some agents to see traces!
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Agent Workflow Traces
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={expandAll}>
              Expand All
            </Button>
            <Button variant="outline" size="sm" onClick={collapseAll}>
              Collapse All
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {tree.map((node) => (
            <TreeNodeComponent
              key={node.id}
              node={node}
              level={0}
              expanded={expanded}
              onToggle={toggleNode}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

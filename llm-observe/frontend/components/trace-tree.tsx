"use client";

import { useState } from "react";
import { CostEvent } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronRight, ChevronDown, Zap, Clock, DollarSign, Database, MessageSquare, Calendar, Mail, Phone } from "lucide-react";
import { cn } from "@/lib/utils";

interface TreeNode {
  id: string;
  name: string;
  type: "workflow" | "api_call" | "tool_call";
  provider?: string;
  cost?: number;
  duration?: number;
  timestamp?: string;
  children?: TreeNode[];
  metadata?: Record<string, any>;
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
};

const providerColors: Record<string, string> = {
  openai: "bg-green-500",
  pinecone: "bg-purple-500",
  google: "bg-blue-500",
  vapi: "bg-orange-500",
  gmail: "bg-red-500",
};

function buildTree(events: CostEvent[]): TreeNode[] {
  // Group events by workflow_id
  const workflows = new Map<string, CostEvent[]>();
  
  events.forEach(event => {
    const workflowId = event.workflow_id || "orphaned";
    if (!workflows.has(workflowId)) {
      workflows.set(workflowId, []);
    }
    workflows.get(workflowId)!.push(event);
  });

  const tree: TreeNode[] = [];

  workflows.forEach((workflowEvents, workflowId) => {
    // Sort events by timestamp
    workflowEvents.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const workflowNode: TreeNode = {
      id: workflowId,
      name: workflowId === "orphaned" ? "Orphaned Events" : `Workflow: ${workflowId}`,
      type: "workflow",
      cost: workflowEvents.reduce((sum, e) => sum + e.cost_usd, 0),
      duration: workflowEvents.reduce((sum, e) => sum + e.duration_ms, 0),
      timestamp: workflowEvents[0]?.timestamp,
      children: workflowEvents.map((event, idx) => ({
        id: `event-${event.id}`,
        name: event.operation 
          ? `${event.provider} - ${event.operation}`
          : event.model 
          ? `${event.provider} - ${event.model}`
          : event.provider,
        type: "api_call" as const,
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
      })),
    };

    tree.push(workflowNode);
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
  const Icon = node.provider ? providerIcons[node.provider] || Zap : Zap;
  const providerColor = node.provider ? providerColors[node.provider] || "bg-gray-500" : "bg-gray-500";

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-accent/50 transition-colors cursor-pointer",
          level > 0 && "ml-4"
        )}
        style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
        onClick={() => hasChildren && onToggle(node.id)}
      >
        {hasChildren && (
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0"
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
        {!hasChildren && <div className="w-4" />}
        
        <div className={cn("p-1.5 rounded", providerColor)}>
          <Icon className="h-3 w-3 text-white" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm truncate">{node.name}</span>
            {node.type === "workflow" && (
              <Badge variant="outline" className="text-xs">
                {node.children?.length || 0} calls
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
            {node.cost !== undefined && node.cost > 0 && (
              <span className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                ${node.cost.toFixed(4)}
              </span>
            )}
            {node.duration !== undefined && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {node.duration.toFixed(0)}ms
              </span>
            )}
            {node.timestamp && (
              <span>{new Date(node.timestamp).toLocaleTimeString()}</span>
            )}
          </div>
        </div>
      </div>

      {isExpanded && hasChildren && (
        <div className="border-l-2 border-border ml-6">
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
            Workflow Traces
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
        <div className="space-y-1">
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


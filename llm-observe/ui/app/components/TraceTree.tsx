"use client";

import { useState } from "react";
import { SpanSummary, updateSpanName } from "@/lib/api";
import { format } from "date-fns";

interface TraceTreeProps {
  spans: SpanSummary[];
}

function getProviderColor(name: string): string {
  if (name.includes("gpt") || name.includes("llm")) return "text-blue-600 dark:text-blue-400";
  if (name.includes("pinecone")) return "text-green-600 dark:text-green-400";
  return "text-orange-600 dark:text-orange-400";
}

function getProviderIcon(name: string): string {
  if (name.includes("gpt") || name.includes("llm")) return "🧠";
  if (name.includes("pinecone")) return "🌲";
  return "🔧";
}

function formatDuration(ms: number | null): string {
  if (!ms) return "N/A";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function SpanNode({ span, allSpans, onSpanUpdate }: { span: SpanSummary; allSpans: SpanSummary[]; onSpanUpdate?: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(span.name);
  const [isSaving, setIsSaving] = useState(false);
  const children = allSpans.filter((s) => s.parent_span_id === span.span_id);

  const handleSave = async () => {
    if (editedName.trim() === span.name) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await updateSpanName(span.span_id, editedName.trim());
      setIsEditing(false);
      onSpanUpdate?.();
    } catch (error) {
      console.error("Failed to update span name:", error);
      setEditedName(span.name); // Revert on error
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="ml-4 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
      <div
        className="flex items-center gap-2 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded px-2 transition-colors group"
      >
        {children.length > 0 && (
          <button
            className="text-gray-400 hover:text-gray-600 cursor-pointer"
            onClick={() => setExpanded(!expanded)}
            aria-label={expanded ? "Collapse" : "Expand"}
          >
            {expanded ? "▼" : "▶"}
          </button>
        )}
        {children.length === 0 && <span className="w-4" />}
        <span className="text-lg">{getProviderIcon(span.name)}</span>
        {isEditing ? (
          <div className="flex items-center gap-2 flex-1">
            <input
              type="text"
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSave();
                if (e.key === "Escape") {
                  setEditedName(span.name);
                  setIsEditing(false);
                }
              }}
              className="px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 flex-1"
              autoFocus
              disabled={isSaving}
            />
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {isSaving ? "..." : "✓"}
            </button>
            <button
              onClick={() => {
                setEditedName(span.name);
                setIsEditing(false);
              }}
              disabled={isSaving}
              className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            >
              ✕
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 flex-1">
              <span 
                className={`font-medium ${getProviderColor(span.name)}`}
              >
                {span.name}
              </span>
              {/* Show function context based on span order and type */}
              {span.name === "llm.request" && (
                <span className="text-xs text-gray-500 dark:text-gray-400 italic">
                  (GPT call)
                </span>
              )}
              {span.name === "pinecone.query" && (
                <span className="text-xs text-gray-500 dark:text-gray-400 italic">
                  (vector search)
                </span>
              )}
              {span.name === "agent.workflow" && (
                <span className="text-xs text-gray-500 dark:text-gray-400 italic">
                  (workflow root)
                </span>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditing(true);
                }}
                className="text-xs text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors ml-1"
                title="Click to rename this span"
              >
                ✏️
              </button>
            </div>
            {span.model && (
              <span className="text-xs text-gray-500 dark:text-gray-400">({span.model})</span>
            )}
          </>
        )}
        <span className="text-xs text-gray-500 dark:text-gray-400 ml-auto">
          {formatDuration(span.duration_ms)}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          ${span.cost_usd.toFixed(4)}
        </span>
      </div>
      {expanded && children.length > 0 && (
        <div className="ml-4 border-l-2 border-gray-200 dark:border-gray-700 pl-2">
          {children.map((child) => (
            <SpanNode key={child.span_id} span={child} allSpans={allSpans} onSpanUpdate={onSpanUpdate} />
          ))}
        </div>
      )}
    </div>
  );
}

export function TraceTree({ spans, onUpdate }: TraceTreeProps & { onUpdate?: () => void }) {
  const rootSpans = spans.filter((s) => !s.parent_span_id);

  if (spans.length === 0) {
    return <p className="text-gray-500 dark:text-gray-400">No spans found</p>;
  }

  // Sort spans by start_time to show execution order
  const sortedSpans = [...spans].sort((a, b) => a.start_time - b.start_time);

  return (
    <div className="space-y-1">
      <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-800 dark:text-blue-200 font-medium mb-1">
          📋 Execution Flow:
        </p>
        <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
          {rootSpans.length > 0 && (
            <div>1. <strong>{rootSpans[0].name}</strong> - Workflow container</div>
          )}
          {sortedSpans
            .filter((s) => s.parent_span_id)
            .map((span, idx) => {
              const stepNum = idx + 2;
              let stepName = "";
              if (span.name === "llm.request") {
                stepName = idx === 0 ? "Query Generation" : "Summarization";
              } else if (span.name === "pinecone.query") {
                stepName = "Vector Search";
              } else {
                stepName = span.name;
              }
              return (
                <div key={span.span_id}>
                  {stepNum}. <strong>{span.name}</strong> - {stepName}
                </div>
              );
            })}
        </div>
      </div>
      {rootSpans.map((root) => (
        <SpanNode key={root.span_id} span={root} allSpans={spans} onSpanUpdate={onUpdate} />
      ))}
    </div>
  );
}


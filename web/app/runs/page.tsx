"use client";

import { useEffect, useState, useMemo, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/PageHeader";
import { SearchInput } from "@/components/filters/SearchInput";
import { fetchRuns, type Run } from "@/lib/api";
import { formatCost, formatDuration } from "@/lib/stats";
import { format } from "date-fns";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Download,
  RefreshCw,
} from "lucide-react";
import { exportToCSV } from "@/lib/export";

type SortField = "started_at" | "total_cost" | "call_count" | "top_section";
type SortDirection = "asc" | "desc";

function RunsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { getToken } = useAuth();
  const parentRef = useRef<HTMLDivElement>(null);

  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<SortField>("started_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  useEffect(() => {
    async function loadRuns() {
      try {
        setLoading(true);
        setError(null);
        
        const token = await getToken();
        if (!token) {
          setError("Not authenticated. Please sign in.");
          setLoading(false);
          return;
        }
        const data = await fetchRuns(5000, null, token); // Load many runs for virtualization demo
        setRuns(data);
      } catch (err) {
        console.error("[Runs] Error loading runs:", err);
        setError(err instanceof Error ? err.message : "Failed to load runs");
      } finally {
        setLoading(false);
      }
    }

    loadRuns();
  }, [getToken]);

  // Filter and sort runs
  const filteredAndSortedRuns = useMemo(() => {
    let result = [...runs];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (run) =>
          run.run_id.toLowerCase().includes(query) ||
          run.top_section.toLowerCase().includes(query) ||
          run.sections.some((s) => s.toLowerCase().includes(query))
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case "started_at":
          comparison = new Date(a.started_at).getTime() - new Date(b.started_at).getTime();
          break;
        case "total_cost":
          comparison = a.total_cost - b.total_cost;
          break;
        case "call_count":
          comparison = a.call_count - b.call_count;
          break;
        case "top_section":
          comparison = a.top_section.localeCompare(b.top_section);
          break;
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });

    return result;
  }, [runs, searchQuery, sortField, sortDirection]);

  // Virtualization
  const virtualizer = useVirtualizer({
    count: filteredAndSortedRuns.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60, // Estimated row height
    overscan: 10,
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const handleExport = () => {
    exportToCSV(filteredAndSortedRuns);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ArrowUpDown className="h-4 w-4 ml-1 opacity-30" />;
    return sortDirection === "asc" ? (
      <ArrowUp className="h-4 w-4 ml-1" />
    ) : (
      <ArrowDown className="h-4 w-4 ml-1" />
    );
  };

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <PageHeader title="Runs" />
        <Card className="mt-6">
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        title="Runs"
        description={`${filteredAndSortedRuns.length} runs found`}
        breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Runs" }]}
        actions={
          <>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.reload()}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </>
        }
      />

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <SearchInput
            placeholder="Search by run ID, section..."
            value={searchQuery}
            onChange={setSearchQuery}
            className="max-w-md"
          />
        </CardContent>
      </Card>

      {/* Virtualized Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Runs</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {filteredAndSortedRuns.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              {searchQuery
                ? "No runs match your search."
                : "No runs found. Run the test script to generate sample data."}
            </div>
          ) : (
            <>
              {/* Header Row */}
              <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b bg-muted/50 font-medium text-sm">
                <div
                  className="col-span-2 flex items-center cursor-pointer hover:text-primary"
                  onClick={() => handleSort("started_at")}
                >
                  Time
                  <SortIcon field="started_at" />
                </div>
                <div className="col-span-3">Run ID</div>
                <div
                  className="col-span-2 flex items-center justify-end cursor-pointer hover:text-primary"
                  onClick={() => handleSort("total_cost")}
                >
                  Cost
                  <SortIcon field="total_cost" />
                </div>
                <div
                  className="col-span-1 flex items-center justify-end cursor-pointer hover:text-primary"
                  onClick={() => handleSort("call_count")}
                >
                  Calls
                  <SortIcon field="call_count" />
                </div>
                <div
                  className="col-span-2 flex items-center cursor-pointer hover:text-primary"
                  onClick={() => handleSort("top_section")}
                >
                  Top Section
                  <SortIcon field="top_section" />
                </div>
                <div className="col-span-2">Sections</div>
              </div>

              {/* Virtualized Rows */}
              <div
                ref={parentRef}
                className="h-[600px] overflow-auto"
                style={{ contain: "strict" }}
              >
                <div
                  style={{
                    height: `${virtualizer.getTotalSize()}px`,
                    width: "100%",
                    position: "relative",
                  }}
                >
                  {virtualizer.getVirtualItems().map((virtualRow) => {
                    const run = filteredAndSortedRuns[virtualRow.index];
                    return (
                      <div
                        key={virtualRow.key}
                        data-index={virtualRow.index}
                        ref={virtualizer.measureElement}
                        className="absolute top-0 left-0 w-full"
                        style={{
                          transform: `translateY(${virtualRow.start}px)`,
                        }}
                      >
                        <Link
                          href={`/runs/${run.run_id}`}
                          className="grid grid-cols-12 gap-4 px-6 py-3 border-b hover:bg-muted/50 transition-colors"
                        >
                          <div className="col-span-2 text-sm text-muted-foreground">
                            {format(new Date(run.started_at), "MMM d, HH:mm")}
                          </div>
                          <div className="col-span-3 font-mono text-xs">
                            {run.run_id.slice(0, 12)}...
                          </div>
                          <div className="col-span-2 text-right font-semibold">
                            {formatCost(run.total_cost)}
                          </div>
                          <div className="col-span-1 text-right text-sm">
                            {run.call_count}
                          </div>
                          <div className="col-span-2">
                            <Badge variant="secondary" className="text-xs">
                              {run.top_section}
                            </Badge>
                          </div>
                          <div className="col-span-2 flex gap-1 flex-wrap">
                            {run.sections.slice(0, 2).map((section) => (
                              <Badge
                                key={section}
                                variant="outline"
                                className="text-xs"
                              >
                                {section}
                              </Badge>
                            ))}
                            {run.sections.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{run.sections.length - 2}
                              </Badge>
                            )}
                          </div>
                        </Link>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function RunsPage() {
  return (
    <Suspense fallback={<div className="p-6"><Skeleton className="h-96 w-full" /></div>}>
      <RunsPageContent />
    </Suspense>
  );
}

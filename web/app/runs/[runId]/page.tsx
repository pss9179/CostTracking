"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchRunDetail, type RunDetail } from "@/lib/api";
import { GraphTreeVisualization } from "@/components/GraphTreeVisualization";
import { WaterfallChart } from "@/components/charts/WaterfallChart";

export default function RunDetailPage() {
  const params = useParams();
  const runId = params.runId as string;
  
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      setError("No run ID provided");
      setLoading(false);
      return;
    }

    async function loadDetail() {
      try {
        const data = await fetchRunDetail(runId);
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load run detail");
      } finally {
        setLoading(false);
      }
    }

    loadDetail();
  }, [runId]);

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map(i => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-6 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-4">Run Detail</h1>
        <Card>
          <CardContent className="pt-6">
            <p className="text-red-600">{error || "Run not found"}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Run Detail</h1>
          <p className="text-sm text-muted-foreground font-mono mt-1">
            {runId}
          </p>
        </div>
        <Link
          href="/runs"
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to Runs
        </Link>
      </div>

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground">Total Cost</p>
              <p className="text-2xl font-bold">${detail.total_cost.toFixed(6)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Calls</p>
              <p className="text-2xl font-bold">
                {detail.events.length}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Sections</p>
              <p className="text-2xl font-bold">
                {detail.breakdown.by_section.length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Breakdown by Section</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Section</TableHead>
                <TableHead className="text-right">Cost</TableHead>
                <TableHead className="text-right">Calls</TableHead>
                <TableHead className="text-right">% of Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {detail.breakdown.by_section.map((item) => (
                <TableRow key={item.section}>
                  <TableCell>
                    <Badge variant="secondary">{item.section}</Badge>
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    ${item.cost.toFixed(6)}
                  </TableCell>
                  <TableCell className="text-right">{item.count}</TableCell>
                  <TableCell className="text-right">
                    {item.percentage.toFixed(1)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Events View - Hierarchical or Flat */}
      <Tabs defaultValue="hierarchy">
        <TabsList>
          <TabsTrigger value="hierarchy">Hierarchical Trace</TabsTrigger>
          <TabsTrigger value="waterfall">Waterfall Timeline</TabsTrigger>
          <TabsTrigger value="flat">Flat Event List</TabsTrigger>
        </TabsList>

        <TabsContent value="hierarchy">
          <Card>
            <CardHeader>
              <CardTitle>Hierarchical Trace View</CardTitle>
            </CardHeader>
            <CardContent>
              <GraphTreeVisualization events={detail.events.map(e => ({
                ...e,
                input_tokens: e.input_tokens ?? 0,
                output_tokens: e.output_tokens ?? 0,
              }))} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="waterfall">
          <Card>
            <CardHeader>
              <CardTitle>Waterfall Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <WaterfallChart events={detail.events} height={500} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="flat">
          <Card>
            <CardHeader>
              <CardTitle>Flat Event List (Latest 50)</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Section</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>Endpoint</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead className="text-right">Latency (ms)</TableHead>
                    <TableHead className="text-right">Tokens</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detail.events.map((event) => (
                    <TableRow key={event.id}>
                      <TableCell className="text-xs">
                        {formatDate(event.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-xs">
                          {event.section}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {event.provider}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">{event.endpoint}</TableCell>
                      <TableCell className="text-xs">
                        {event.model || "—"}
                      </TableCell>
                      <TableCell className="text-right text-xs">
                        {event.latency_ms.toFixed(0)}
                      </TableCell>
                      <TableCell className="text-right text-xs">
                        {event.input_tokens + event.output_tokens > 0
                          ? `${event.input_tokens} / ${event.output_tokens}`
                          : "—"}
                      </TableCell>
                      <TableCell className="text-right font-semibold text-xs">
                        ${event.cost_usd.toFixed(6)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={event.status === "ok" ? "default" : "destructive"}
                          className="text-xs"
                        >
                          {event.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}


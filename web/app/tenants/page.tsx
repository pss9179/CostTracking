"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { TenantSelector } from "@/components/TenantSelector";

interface TenantStats {
  tenant_id: string;
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
}

export default function TenantsPage() {
  const [stats, setStats] = useState<TenantStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/tenants/stats?days=7")
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Tenant Statistics (Last 7 Days)</h1>
        <TenantSelector />
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Cost by Tenant</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : stats.length === 0 ? (
            <p className="text-muted-foreground">
              No tenant data available. Set tenant_id when calling observe() or via LLMOBSERVE_TENANT_ID env var.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tenant ID</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                  <TableHead className="text-right">API Calls</TableHead>
                  <TableHead className="text-right">Avg Latency (ms)</TableHead>
                  <TableHead className="text-right">Customers</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.map(tenant => (
                  <TableRow key={tenant.tenant_id}>
                    <TableCell className="font-medium">{tenant.tenant_id}</TableCell>
                    <TableCell className="text-right">${tenant.total_cost.toFixed(6)}</TableCell>
                    <TableCell className="text-right">{tenant.call_count}</TableCell>
                    <TableCell className="text-right">{tenant.avg_latency_ms.toFixed(2)}</TableCell>
                    <TableCell className="text-right">
                      <Link
                        href={`/tenants/${tenant.tenant_id}/customers`}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        View Customers →
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


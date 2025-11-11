"use client";

import { useState, useEffect } from "react";
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
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { fetchCustomerStatsByTenant, type CustomerStats } from "@/lib/api";

export default function TenantCustomersPage() {
  const params = useParams();
  const tenantId = params.tenantId as string;
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCustomerStats() {
      try {
        const data = await fetchCustomerStatsByTenant(tenantId, 7);
        setCustomers(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load customer stats");
      } finally {
        setLoading(false);
      }
    }

    loadCustomerStats();
    const interval = setInterval(loadCustomerStats, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [tenantId]);

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-5 w-32" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Customers for {tenantId}</h1>
          <p className="text-muted-foreground">Cost breakdown by customer (Last 7 days)</p>
        </div>
        <Link href="/tenants" className="text-sm text-blue-600 hover:underline">
          ← Back to Tenants
        </Link>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Customer Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          {customers.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No customer data for this tenant. Use <code className="bg-gray-100 px-1 rounded">set_customer_id()</code> to track end-user costs.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer ID</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                  <TableHead className="text-right">API Calls</TableHead>
                  <TableHead className="text-right">Avg Latency (ms)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {customers.map((customer) => (
                  <TableRow key={customer.customer_id}>
                    <TableCell className="font-medium">{customer.customer_id}</TableCell>
                    <TableCell className="text-right">${customer.total_cost.toFixed(6)}</TableCell>
                    <TableCell className="text-right">{customer.call_count.toLocaleString()}</TableCell>
                    <TableCell className="text-right">{customer.avg_latency_ms.toFixed(2)}</TableCell>
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


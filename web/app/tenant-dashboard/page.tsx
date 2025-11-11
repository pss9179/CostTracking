"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

interface CustomerStats {
  customer_id: string;
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
}

interface TenantStats {
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
  customer_count: number;
  top_customer: {
    customer_id: string | null;
    cost: number;
  };
  period_days: number;
}

export default function TenantDashboardPage() {
  const router = useRouter();
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [tenantName, setTenantName] = useState<string | null>(null);
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [stats, setStats] = useState<TenantStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if logged in
    const apiKey = localStorage.getItem("tenant_api_key");
    const storedTenantId = localStorage.getItem("tenant_id");
    const storedTenantName = localStorage.getItem("tenant_name");

    if (!apiKey || !storedTenantId) {
      router.push("/tenant-login");
      return;
    }

    setTenantId(storedTenantId);
    setTenantName(storedTenantName);

    async function loadData() {
      try {
        const apiKey = localStorage.getItem("tenant_api_key");
        const headers = {
          "X-API-Key": apiKey!
        };

        const [customersRes, statsRes] = await Promise.all([
          fetch("http://localhost:8000/dashboard/customers?days=7", { headers }),
          fetch("http://localhost:8000/dashboard/stats?days=7", { headers })
        ]);

        if (!customersRes.ok || !statsRes.ok) {
          throw new Error("Failed to fetch data");
        }

        const [customersData, statsData] = await Promise.all([
          customersRes.json(),
          statsRes.json()
        ]);

        setCustomers(customersData);
        setStats(statsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("tenant_api_key");
    localStorage.removeItem("tenant_id");
    localStorage.removeItem("tenant_name");
    router.push("/tenant-login");
  };

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-6 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <Button onClick={handleLogout} className="mt-4">
            Back to Login
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{tenantName || tenantId}</h1>
          <p className="text-muted-foreground">Customer Cost Dashboard</p>
        </div>
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </div>

      {/* KPI Cards */}
      {stats && (
        <div className="grid gap-6 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Cost (7 days)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${stats.total_cost.toFixed(4)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total API Calls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.call_count.toLocaleString()}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Customers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.customer_count}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Avg Latency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.avg_latency_ms.toFixed(0)}ms
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Customer Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Cost by Customer (Last 7 Days)</CardTitle>
          <p className="text-sm text-muted-foreground">
            See how much each of your users is contributing to your API costs
          </p>
        </CardHeader>
        <CardContent>
          {customers.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                No customer data found. Start tracking with:
              </p>
              <code className="mt-2 block bg-gray-100 p-2 rounded">
                set_customer_id("user_123")
              </code>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer ID</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                  <TableHead className="text-right">API Calls</TableHead>
                  <TableHead className="text-right">Avg Latency</TableHead>
                  <TableHead className="text-right">% of Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {customers.map((customer) => {
                  const percentage = stats
                    ? (customer.total_cost / stats.total_cost) * 100
                    : 0;
                  return (
                    <TableRow key={customer.customer_id}>
                      <TableCell className="font-medium">
                        {customer.customer_id}
                      </TableCell>
                      <TableCell className="text-right">
                        ${customer.total_cost.toFixed(6)}
                      </TableCell>
                      <TableCell className="text-right">
                        {customer.call_count.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        {customer.avg_latency_ms.toFixed(0)}ms
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={`font-semibold ${
                            percentage > 50
                              ? "text-red-600"
                              : percentage > 25
                              ? "text-orange-600"
                              : "text-green-600"
                          }`}
                        >
                          {percentage.toFixed(1)}%
                        </span>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Top Customer Callout */}
      {stats && stats.top_customer.customer_id && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-900">
                  Highest Cost Customer
                </p>
                <p className="text-2xl font-bold text-blue-900 mt-1">
                  {stats.top_customer.customer_id}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-blue-700">Total Cost</p>
                <p className="text-2xl font-bold text-blue-900">
                  ${stats.top_customer.cost.toFixed(4)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}


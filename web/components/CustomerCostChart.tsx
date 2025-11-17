"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { formatCost } from "@/lib/stats";
import { Users } from "lucide-react";

interface CustomerStats {
  customer_id: string;
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
}

const COLORS = ["#3b82f6", "#a855f7", "#f97316", "#10b981", "#6366f1", "#ec4899", "#f59e0b"];

export function CustomerCostChart() {
  const { getToken } = useAuth();
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"bar" | "pie">("bar");

  useEffect(() => {
    async function loadCustomers() {
      try {
        // Get Clerk token for authentication
        const token = await getToken({ template: "default" });
        if (!token) {
          setError("Not authenticated");
          setLoading(false);
          return;
        }
        
        // Fetch customer stats from collector API
        const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
        const response = await fetch(`${collectorUrl}/stats/by-customer?hours=720`, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }); // 30 days
        if (!response.ok) throw new Error("Failed to fetch customer data");
        const data = await response.json();
        
        // Filter out test/fake customers and only show real ones
        // Real customers should have meaningful IDs, not test patterns
        const realCustomers = data.filter((c: any) => {
          const id = c.customer_id || '';
          // Exclude test patterns
          return id && 
                 !id.startsWith('test_') && 
                 !id.startsWith('rag_') &&
                 !id.startsWith('customer_') &&
                 id.length > 5; // Real customer IDs are usually longer
        });
        
        setCustomers(realCustomers);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }

    loadCustomers();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cost by Customer (30d)</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cost by Customer (30d)</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">Error: {error}</p>
        </CardContent>
      </Card>
    );
  }

  if (customers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Cost by Customer (30d)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            No customer data available yet. Add customer_id to your trace events to see per-customer costs.
          </p>
        </CardContent>
      </Card>
    );
  }

  const chartData = customers
    .sort((a, b) => b.total_cost - a.total_cost)
    .slice(0, 10)  // Top 10 customers
    .map(c => ({
      name: c.customer_id.length > 20 ? c.customer_id.slice(0, 20) + "..." : c.customer_id,
      cost: c.total_cost,
      calls: c.call_count,
      fullName: c.customer_id,
    }));

  const totalCost = customers.reduce((sum, c) => sum + c.total_cost, 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Cost by Customer (30d)
          </CardTitle>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode("bar")}
              className={`px-3 py-1 text-xs rounded ${
                viewMode === "bar"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Bar
            </button>
            <button
              onClick={() => setViewMode("pie")}
              className={`px-3 py-1 text-xs rounded ${
                viewMode === "pie"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Pie
            </button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          Total: {formatCost(totalCost)} across {customers.length} customer{customers.length !== 1 ? 's' : ''}
        </p>
      </CardHeader>
      <CardContent>
        {viewMode === "bar" ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={100}
                tick={{ fontSize: 12 }}
              />
              <YAxis tickFormatter={(v) => formatCost(v)} />
              <Tooltip
                formatter={(value: any) => formatCost(Number(value))}
                labelFormatter={(label, payload) => {
                  const data = payload?.[0]?.payload;
                  return data?.fullName || label;
                }}
              />
              <Bar dataKey="cost" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="cost"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => formatCost(Number(value))} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}


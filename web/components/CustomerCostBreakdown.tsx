"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCost } from "@/lib/stats";

interface CustomerStats {
  customer_id: string;
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
}

interface CustomerCostBreakdownProps {
  tenantId: string;
}

export function CustomerCostBreakdown({ tenantId }: CustomerCostBreakdownProps) {
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCustomers() {
      try {
        const response = await fetch(`/api/tenants/${tenantId}/customers`);
        if (!response.ok) throw new Error("Failed to fetch customer data");
        const data = await response.json();
        setCustomers(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }

    loadCustomers();
  }, [tenantId]);

  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-red-600">Error: {error}</p>
    );
  }

  if (customers.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-4">
        No customer data available for this tenant.
      </p>
    );
  }

  const totalCost = customers.reduce((sum, c) => sum + c.total_cost, 0);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer</TableHead>
          <TableHead className="text-right">Total Cost</TableHead>
          <TableHead className="text-right">Calls</TableHead>
          <TableHead className="text-right">Avg/Call</TableHead>
          <TableHead className="text-right">% of Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {customers.map((customer) => {
          const percentage = totalCost > 0 ? (customer.total_cost / totalCost) * 100 : 0;
          const avgCostPerCall = customer.call_count > 0 ? customer.total_cost / customer.call_count : 0;
          
          return (
            <TableRow key={customer.customer_id}>
              <TableCell>
                <Badge variant="outline">{customer.customer_id}</Badge>
              </TableCell>
              <TableCell className="text-right font-semibold">
                {formatCost(customer.total_cost)}
              </TableCell>
              <TableCell className="text-right">{customer.call_count}</TableCell>
              <TableCell className="text-right text-muted-foreground">
                {formatCost(avgCostPerCall)}
              </TableCell>
              <TableCell className="text-right text-muted-foreground">
                {percentage.toFixed(1)}%
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}


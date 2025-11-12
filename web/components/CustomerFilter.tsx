"use client";

import { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Users } from "lucide-react";

interface CustomerStats {
  customer_id: string;
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
}

interface CustomerFilterProps {
  selectedCustomer: string | null;
  onCustomerChange: (customerId: string | null) => void;
  showAllOption?: boolean;
}

export function CustomerFilter({
  selectedCustomer,
  onCustomerChange,
  showAllOption = true,
}: CustomerFilterProps) {
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCustomers() {
      try {
        const response = await fetch('/api/customers');
        if (response.ok) {
          const data = await response.json();
          setCustomers(data);
        }
      } catch (err) {
        console.error("Failed to load customers:", err);
      } finally {
        setLoading(false);
      }
    }

    loadCustomers();
  }, []);

  if (loading) {
    return (
      <Select disabled>
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Loading customers..." />
        </SelectTrigger>
      </Select>
    );
  }

  if (customers.length === 0) {
    return null;  // Don't show filter if no customers
  }

  return (
    <Select
      value={selectedCustomer || "all"}
      onValueChange={(value) => onCustomerChange(value === "all" ? null : value)}
    >
      <SelectTrigger className="w-48">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-muted-foreground" />
          <SelectValue placeholder="All Customers" />
        </div>
      </SelectTrigger>
      <SelectContent>
        {showAllOption && (
          <SelectItem value="all">All Customers</SelectItem>
        )}
        {customers.map((customer) => (
          <SelectItem key={customer.customer_id} value={customer.customer_id}>
            {customer.customer_id} ({customer.total_cost.toFixed(4)})
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}


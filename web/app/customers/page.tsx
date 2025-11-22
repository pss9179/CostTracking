"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Search } from "lucide-react";
import { useState } from "react";

// Mock data
const MOCK_CUSTOMERS = [
  {
    id: "cus_12345678",
    name: "Acme Corp",
    total_cost: 1245.50,
    calls: 15420,
    avg_latency: 450,
    last_active: "2 mins ago",
    trend: "+12%",
    status: "active"
  },
  {
    id: "cus_87654321",
    name: "Startup Inc",
    total_cost: 850.20,
    calls: 8200,
    avg_latency: 320,
    last_active: "1 hour ago",
    trend: "+5%",
    status: "active"
  },
  {
    id: "cus_98765432",
    name: "Enterprise Ltd",
    total_cost: 3200.00,
    calls: 45000,
    avg_latency: 550,
    last_active: "5 mins ago",
    trend: "+8%",
    status: "active"
  },
  {
    id: "cus_56781234",
    name: "Dev Team A",
    total_cost: 45.00,
    calls: 120,
    avg_latency: 200,
    last_active: "2 days ago",
    trend: "-2%",
    status: "inactive"
  },
  {
    id: "cus_43218765",
    name: "Test User",
    total_cost: 12.50,
    calls: 50,
    avg_latency: 150,
    last_active: "1 week ago",
    trend: "0%",
    status: "inactive"
  }
];

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredCustomers = MOCK_CUSTOMERS.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Customers</h1>
          <p className="text-gray-600 mt-2">
            Track API usage and costs per customer.
          </p>
        </div>
        <div className="flex gap-3">
          <button className="bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">
            Export CSV
          </button>
          <button className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors">
            Add Customer
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-0 shadow-sm bg-white">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground mb-1">Total Customers</p>
            <h3 className="text-2xl font-bold">1,245</h3>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-white">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground mb-1">Active (30d)</p>
            <h3 className="text-2xl font-bold">854</h3>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-white">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground mb-1">Avg Cost/Customer</p>
            <h3 className="text-2xl font-bold">$42.50</h3>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-white">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground mb-1">Total Revenue</p>
            <h3 className="text-2xl font-bold">$52.4k</h3>
          </CardContent>
        </Card>
      </div>

      {/* Table Section */}
      <div className="rounded-lg border border-gray-100 bg-white overflow-hidden">
        <div className="border-b border-gray-100 bg-gray-50/50 px-6 py-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">All Customers</h3>
            <div className="relative w-72">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by name or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-white"
              />
            </div>
          </div>
        </div>
        <Table>
          <TableHeader className="bg-gray-50/50">
            <TableRow className="border-gray-100 hover:bg-transparent">
              <TableHead className="font-medium text-gray-500">Customer</TableHead>
              <TableHead className="font-medium text-gray-500">Status</TableHead>
              <TableHead className="text-right font-medium text-gray-500">Total Cost</TableHead>
              <TableHead className="text-right font-medium text-gray-500">API Calls</TableHead>
              <TableHead className="text-right font-medium text-gray-500">Avg Latency</TableHead>
              <TableHead className="text-right font-medium text-gray-500">Last Active</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCustomers.map((customer) => (
              <TableRow key={customer.id} className="border-gray-50 hover:bg-gray-50/50">
                <TableCell>
                  <div>
                    <div className="font-medium text-gray-900">{customer.name}</div>
                    <div className="text-xs text-gray-500 font-mono">{customer.id}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant="secondary"
                    className="bg-gray-100 text-gray-700 hover:bg-gray-100"
                  >
                    {customer.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right text-gray-600">
                  ${customer.total_cost.toFixed(2)}
                </TableCell>
                <TableCell className="text-right text-gray-600">
                  {customer.calls.toLocaleString()}
                </TableCell>
                <TableCell className="text-right text-gray-600">
                  {customer.avg_latency}ms
                </TableCell>
                <TableCell className="text-right text-gray-500">
                  {customer.last_active}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

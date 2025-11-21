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
import { Search, Users, ArrowUpRight, ArrowDownRight, DollarSign, Activity } from "lucide-react";
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
          <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm">
            Add Customer
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-indigo-100 bg-indigo-50/50">
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-indigo-600 mb-1">Total Customers</p>
                <h3 className="text-3xl font-bold text-gray-900">1,245</h3>
              </div>
              <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                <Users className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <ArrowUpRight className="h-4 w-4 mr-1" />
              <span className="font-medium">+12%</span>
              <span className="text-gray-500 ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">Active (30d)</p>
                <h3 className="text-3xl font-bold text-gray-900">854</h3>
              </div>
              <div className="p-2 bg-green-100 rounded-lg text-green-600">
                <Activity className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <ArrowUpRight className="h-4 w-4 mr-1" />
              <span className="font-medium">+5%</span>
              <span className="text-gray-500 ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">Avg Cost/Customer</p>
                <h3 className="text-3xl font-bold text-gray-900">$42.50</h3>
              </div>
              <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                <DollarSign className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-red-600">
              <ArrowDownRight className="h-4 w-4 mr-1" />
              <span className="font-medium">-2%</span>
              <span className="text-gray-500 ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">Total Revenue</p>
                <h3 className="text-3xl font-bold text-gray-900">$52.4k</h3>
              </div>
              <div className="p-2 bg-purple-100 rounded-lg text-purple-600">
                <DollarSign className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <ArrowUpRight className="h-4 w-4 mr-1" />
              <span className="font-medium">+18%</span>
              <span className="text-gray-500 ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Table Section */}
      <Card className="border-gray-200 shadow-sm">
        <CardHeader className="border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold text-gray-900">All Customers</CardTitle>
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
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50/50 hover:bg-gray-50/50">
                <TableHead className="w-[250px]">Customer</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Total Cost</TableHead>
                <TableHead className="text-right">API Calls</TableHead>
                <TableHead className="text-right">Avg Latency</TableHead>
                <TableHead className="text-right">Last Active</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCustomers.map((customer) => (
                <TableRow key={customer.id} className="hover:bg-gray-50 transition-colors cursor-pointer">
                  <TableCell>
                    <div>
                      <div className="font-medium text-gray-900">{customer.name}</div>
                      <div className="text-xs text-gray-500 font-mono">{customer.id}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={customer.status === 'active'
                        ? "bg-green-100 text-green-700 hover:bg-green-100"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-100"}
                    >
                      {customer.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-medium text-gray-900">
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
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useUser } from "@clerk/nextjs";
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
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { fetchRuns, fetchRunDetail } from "@/lib/api";
import { formatCost, formatDuration } from "@/lib/stats";
import { Search, TrendingUp, DollarSign, Activity, Users } from "lucide-react";
import { KPICard } from "@/components/layout/KPICard";

interface CustomerStats {
  customer_id: string;
  total_cost: number;
  call_count: number;
  avg_latency: number;
  first_seen: string;
  last_seen: string;
  providers: string[];
}

export default function CustomersPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const { user, isLoaded } = useUser();
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!isLoaded) return;
    if (!user) {
      router.push("/sign-in");
      return;
    }
  }, [isLoaded, user, router]);

  useEffect(() => {
    if (!isLoaded || !user) return;

    async function loadCustomerData() {
      try {
        setLoading(true);
        const token = await getToken();
        if (!token) {
          console.error("No Clerk token available");
          return;
        }
        
        // Fetch all runs
        const runs = await fetchRuns(1000, null, token);
        
        // Fetch events for each run
        const allEvents: any[] = [];
        for (const run of runs.slice(0, 100)) { // Limit to prevent overload
          try {
            const detail = await fetchRunDetail(run.run_id, null, token);
            allEvents.push(...detail.events);
          } catch (err) {
            // Skip failed runs
          }
        }

        // Aggregate by customer_id
        const customerMap = new Map<string, {
          total_cost: number;
          call_count: number;
          latencies: number[];
          first_seen: Date;
          last_seen: Date;
          providers: Set<string>;
        }>();

        allEvents.forEach((event) => {
          const customerId = event.customer_id || "_no_customer";
          const existing = customerMap.get(customerId) || {
            total_cost: 0,
            call_count: 0,
            latencies: [],
            first_seen: new Date(event.created_at),
            last_seen: new Date(event.created_at),
            providers: new Set(),
          };

          existing.total_cost += event.cost_usd || 0;
          existing.call_count += 1;
          existing.latencies.push(event.latency_ms);
          existing.providers.add(event.provider);
          
          const eventDate = new Date(event.created_at);
          if (eventDate < existing.first_seen) existing.first_seen = eventDate;
          if (eventDate > existing.last_seen) existing.last_seen = eventDate;

          customerMap.set(customerId, existing);
        });

        // Convert to array and calculate averages
        const customerStats: CustomerStats[] = Array.from(customerMap.entries())
          .filter(([id]) => id !== "_no_customer") // Exclude events without customer_id
          .map(([customer_id, data]) => ({
            customer_id,
            total_cost: data.total_cost,
            call_count: data.call_count,
            avg_latency: data.latencies.length > 0
              ? data.latencies.reduce((a, b) => a + b, 0) / data.latencies.length
              : 0,
            first_seen: data.first_seen.toISOString(),
            last_seen: data.last_seen.toISOString(),
            providers: Array.from(data.providers),
          }))
          .sort((a, b) => b.total_cost - a.total_cost); // Sort by cost descending

        setCustomers(customerStats);
      } catch (err) {
        console.error("Failed to load customer data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadCustomerData();
  }, [user]);

  // Filter customers by search query
  const filteredCustomers = customers.filter((customer) =>
    customer.customer_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate total stats
  const totalStats = {
    total_customers: customers.length,
    total_cost: customers.reduce((sum, c) => sum + c.total_cost, 0),
    total_calls: customers.reduce((sum, c) => sum + c.call_count, 0),
    avg_cost_per_customer: customers.length > 0
      ? customers.reduce((sum, c) => sum + c.total_cost, 0) / customers.length
      : 0,
  };

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="p-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="p-8 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Customer Cost Breakdown</h1>
          <p className="text-muted-foreground mt-2">
            Track API costs per customer to identify high-usage users and optimize pricing
          </p>
        </div>

        {/* KPIs */}
        <div className="rounded-2xl border border-slate-200 bg-white/90 px-5 py-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">Total Customers</div>
              <div className="text-3xl font-bold text-gray-900">{totalStats.total_customers}</div>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">Total Cost</div>
              <div className="text-3xl font-bold text-gray-900">{formatCost(totalStats.total_cost)}</div>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">Total API Calls</div>
              <div className="text-3xl font-bold text-gray-900">{totalStats.total_calls.toLocaleString()}</div>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">Avg Cost/Customer</div>
              <div className="text-3xl font-bold text-gray-900">{formatCost(totalStats.avg_cost_per_customer)}</div>
            </div>
          </div>
        </div>

        {/* Customer Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>All Customers ({filteredCustomers.length})</span>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search customers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredCustomers.length === 0 ? (
              <div className="text-center py-12">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Customers Found</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {searchQuery
                    ? "No customers match your search query"
                    : "Start tracking customers by calling set_customer_id() in your code"}
                </p>
                <div className="bg-gray-50 rounded p-4 text-left max-w-xl mx-auto">
                  <p className="text-sm font-medium mb-2">Quick Setup:</p>
                  <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-x-auto">
{`from llmobserve import set_customer_id

@app.post("/api/chat")
def handle_chat(request):
    set_customer_id(request.user_id)
    # Your API calls here...`}
                  </pre>
                </div>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer ID</TableHead>
                    <TableHead className="text-right">Total Cost</TableHead>
                    <TableHead className="text-right">API Calls</TableHead>
                    <TableHead className="text-right">Avg Cost/Call</TableHead>
                    <TableHead className="text-right">Avg Latency</TableHead>
                    <TableHead>Providers</TableHead>
                    <TableHead>First Seen</TableHead>
                    <TableHead>Last Seen</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCustomers.map((customer) => (
                    <TableRow
                      key={customer.customer_id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => router.push(`/?customer=${customer.customer_id}`)}
                    >
                      <TableCell className="font-mono font-medium">
                        {customer.customer_id}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCost(customer.total_cost)}
                      </TableCell>
                      <TableCell className="text-right">
                        {customer.call_count.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCost(customer.total_cost / customer.call_count)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatDuration(customer.avg_latency)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 flex-wrap">
                          {customer.providers.map((provider) => (
                            <Badge key={provider} variant="outline" className="text-xs">
                              {provider}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(customer.first_seen).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(customer.last_seen).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}


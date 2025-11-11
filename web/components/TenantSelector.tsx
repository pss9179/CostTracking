"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useEffect, useState } from "react";

export function TenantSelector() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentTenant = searchParams.get("tenant_id") || "all";
  const [tenants, setTenants] = useState<string[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/tenants/list")
      .then(res => res.json())
      .then(data => setTenants(data))
      .catch(() => setTenants([]));
  }, []);

  const handleTenantChange = (value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value === "all") {
      params.delete("tenant_id");
    } else {
      params.set("tenant_id", value);
    }
    const queryString = params.toString();
    router.push(`${pathname}${queryString ? `?${queryString}` : ""}`);
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">Tenant:</span>
      <Select value={currentTenant} onValueChange={handleTenantChange}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="All tenants" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All tenants</SelectItem>
          {tenants.map(tenant => (
            <SelectItem key={tenant} value={tenant}>{tenant}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}


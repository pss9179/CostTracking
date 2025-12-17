"use client";

import { createContext, useContext, useState, ReactNode } from "react";

export type DateRange = "1h" | "6h" | "24h" | "3d" | "7d" | "14d" | "30d" | "90d" | "180d" | "365d";

interface DateRangeContextType {
  dateRange: DateRange;
  setDateRange: (range: DateRange) => void;
}

const DateRangeContext = createContext<DateRangeContextType>({
  dateRange: "7d",
  setDateRange: () => {},
});

export function DateRangeProvider({ children }: { children: ReactNode }) {
  const [dateRange, setDateRange] = useState<DateRange>("7d");

  return (
    <DateRangeContext.Provider value={{ dateRange, setDateRange }}>
      {children}
    </DateRangeContext.Provider>
  );
}

export function useDateRange() {
  const context = useContext(DateRangeContext);
  if (!context) {
    throw new Error("useDateRange must be used within DateRangeProvider");
  }
  return context;
}


"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon } from "lucide-react";
import { format, subHours, subDays } from "date-fns";
import { cn } from "@/lib/utils";

export type TimeRange = {
  from: Date;
  to: Date;
  preset?: string;
};

const PRESETS = [
  { label: "1h", value: "1h", getRange: () => ({ from: subHours(new Date(), 1), to: new Date() }) },
  { label: "24h", value: "24h", getRange: () => ({ from: subDays(new Date(), 1), to: new Date() }) },
  { label: "7d", value: "7d", getRange: () => ({ from: subDays(new Date(), 7), to: new Date() }) },
  { label: "30d", value: "30d", getRange: () => ({ from: subDays(new Date(), 30), to: new Date() }) },
  { label: "90d", value: "90d", getRange: () => ({ from: subDays(new Date(), 90), to: new Date() }) },
];

export function TimeRangeFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Initialize from URL or default to 24h
  const fromParam = searchParams.get("from");
  const toParam = searchParams.get("to");
  const presetParam = searchParams.get("preset") || "24h";
  
  const defaultPreset = PRESETS.find((p) => p.value === presetParam) || PRESETS[1];
  const defaultRange = defaultPreset.getRange();
  
  const [selectedPreset, setSelectedPreset] = useState(presetParam);
  const [customFrom, setCustomFrom] = useState<Date | undefined>(
    fromParam ? new Date(fromParam) : defaultRange.from
  );
  const [customTo, setCustomTo] = useState<Date | undefined>(
    toParam ? new Date(toParam) : defaultRange.to
  );
  const [isCustomOpen, setIsCustomOpen] = useState(false);

  const updateUrl = (from: Date, to: Date, preset?: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("from", from.toISOString());
    params.set("to", to.toISOString());
    if (preset) {
      params.set("preset", preset);
    } else {
      params.delete("preset");
    }
    router.push(`?${params.toString()}`);
  };

  const handlePresetClick = (preset: typeof PRESETS[0]) => {
    const range = preset.getRange();
    setSelectedPreset(preset.value);
    setCustomFrom(range.from);
    setCustomTo(range.to);
    updateUrl(range.from, range.to, preset.value);
  };

  const handleCustomApply = () => {
    if (customFrom && customTo) {
      setSelectedPreset("custom");
      updateUrl(customFrom, customTo);
      setIsCustomOpen(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Preset Buttons */}
      {PRESETS.map((preset) => (
        <Button
          key={preset.value}
          variant={selectedPreset === preset.value ? "default" : "outline"}
          size="sm"
          onClick={() => handlePresetClick(preset)}
        >
          {preset.label}
        </Button>
      ))}

      {/* Custom Date Range Picker */}
      <Popover open={isCustomOpen} onOpenChange={setIsCustomOpen}>
        <PopoverTrigger asChild>
          <Button
            variant={selectedPreset === "custom" ? "default" : "outline"}
            size="sm"
            className={cn(
              "gap-2",
              selectedPreset === "custom" && "border-primary"
            )}
          >
            <CalendarIcon className="h-4 w-4" />
            {selectedPreset === "custom" && customFrom && customTo
              ? `${format(customFrom, "MMM d")} - ${format(customTo, "MMM d")}`
              : "Custom"}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-4" align="end">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">From</label>
              <Calendar
                mode="single"
                selected={customFrom}
                onSelect={setCustomFrom}
                disabled={(date) => date > new Date() || (customTo ? date > customTo : false)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">To</label>
              <Calendar
                mode="single"
                selected={customTo}
                onSelect={setCustomTo}
                disabled={(date) =>
                  date > new Date() || (customFrom ? date < customFrom : false)
                }
              />
            </div>
            <Button
              onClick={handleCustomApply}
              disabled={!customFrom || !customTo}
              className="w-full"
            >
              Apply
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}


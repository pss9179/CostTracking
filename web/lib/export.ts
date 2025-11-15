import type { Run } from "./api";

/**
 * Export runs to CSV
 */
export function exportToCSV(runs: Run[]): void {
  const headers = ["Run ID", "Started At", "Total Cost", "Call Count", "Top Section"];
  const rows = runs.map((run) => [
    run.run_id,
    run.started_at,
    run.total_cost.toString(),
    run.call_count.toString(),
    run.top_section,
  ]);

  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", `runs_${new Date().toISOString().split("T")[0]}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Export runs to JSON
 */
export function exportToJSON(runs: Run[]): void {
  const jsonContent = JSON.stringify(runs, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", `runs_${new Date().toISOString().split("T")[0]}.json`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


"use client";

import Link from "next/link";
import { DocPage, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "dashboard-overview", title: "Dashboard overview" },
  { id: "filtering-data", title: "Filtering data" },
  { id: "export-data", title: "Exporting data" },
];

export default function ViewingCostsPage() {
  return (
    <DocPage
      title="Viewing costs in the dashboard"
      description="Understand the analytics dashboard and how to explore your LLM spending."
      category="Cost tracking"
      toc={toc}
    >
      <h2 id="dashboard-overview">Dashboard overview</h2>

      <p>
        The <Link href="/dashboard">Dashboard</Link> provides a real-time view of your LLM spending:
      </p>

      <h3>Key metrics</h3>
      <ul>
        <li><strong>Today</strong> — Spending in the last 24 hours</li>
        <li><strong>This Week</strong> — Last 7 days of spending</li>
        <li><strong>This Month</strong> — Last 30 days of spending</li>
        <li><strong>API Calls</strong> — Total number of LLM API calls</li>
      </ul>

      <h3>Spend trend chart</h3>
      <p>
        The main chart shows spending over time. Switch between views:
      </p>
      <ul>
        <li><strong>Total</strong> — Overall spending trend</li>
        <li><strong>Stacked</strong> — Spending broken down by provider (stacked areas)</li>
        <li><strong>By Provider</strong> — Individual lines per provider</li>
      </ul>

      <h3>Provider breakdown</h3>
      <p>
        See which providers you're spending the most on. Click a provider to filter 
        the entire dashboard.
      </p>

      <h3>Model breakdown</h3>
      <p>
        See spending per model. Identify expensive models and find optimization opportunities.
      </p>

      <h2 id="filtering-data">Filtering data</h2>

      <p>Use filters to drill down into your data:</p>

      <ul>
        <li><strong>Time range</strong> — Last 24h, 7 days, 30 days, etc.</li>
        <li><strong>Provider</strong> — Filter by OpenAI, Anthropic, etc.</li>
        <li><strong>Model</strong> — Filter by specific model</li>
      </ul>

      <Callout type="tip">
        Filters apply to all charts and metrics on the page. Use them to investigate 
        specific providers or time periods.
      </Callout>

      <h3>Compare mode</h3>
      <p>
        Click "Compare" to see how current spending compares to the previous period. 
        Useful for tracking spending trends over time.
      </p>

      <h2 id="export-data">Exporting data</h2>

      <p>
        Export your data for custom analysis or reporting. Click the export button on 
        any page to download data as CSV or JSON.
      </p>

      <hr />

      <h3>Other pages</h3>

      <ul>
        <li><Link href="/customers"><strong>Customers</strong></Link> — View costs per customer</li>
        <li><Link href="/features"><strong>Features</strong></Link> — View costs per agent/section</li>
        <li><Link href="/caps"><strong>Caps</strong></Link> — Manage spending limits</li>
      </ul>
    </DocPage>
  );
}


"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "overview", title: "Overview" },
  { id: "setting-up-caps", title: "Setting up caps" },
  { id: "cap-types", title: "Cap types" },
  { id: "alerts", title: "Alerts & notifications" },
  { id: "enforcement", title: "Cap enforcement" },
];

export default function SpendingCapsPage() {
  return (
    <DocPage
      title="Spending caps"
      description="Set budget limits to prevent runaway LLM costs with alerts and optional enforcement."
      category="Spending controls"
      toc={toc}
    >
      <h2 id="overview">Overview</h2>

      <p>
        Spending caps help you control LLM costs by setting maximum budgets. When spending 
        approaches or exceeds a cap, you can:
      </p>

      <ul>
        <li><strong>Get alerted</strong> — Receive email notifications</li>
        <li><strong>Block requests</strong> — Optionally prevent further API calls</li>
        <li><strong>Track in dashboard</strong> — See cap status in real-time</li>
      </ul>

      <Callout type="warning" title="Cap enforcement">
        By default, caps are <em>soft limits</em> that trigger alerts. Enable "hard caps" in 
        Settings to actually block API calls when limits are exceeded.
      </Callout>

      <h2 id="setting-up-caps">Setting up caps</h2>

      <p>
        Configure spending caps in your <Link href="/caps">Dashboard → Caps</Link> page:
      </p>

      <ol>
        <li>Click "Add Cap"</li>
        <li>Choose the cap type (Global, Provider, Model, Customer)</li>
        <li>Set the limit amount and time period</li>
        <li>Configure alert thresholds (e.g., alert at 80%, 95%)</li>
        <li>Optionally enable hard enforcement</li>
      </ol>

      <h2 id="cap-types">Cap types</h2>

      <h3>Global caps</h3>

      <p>
        Limit total spending across all providers and customers. Useful for overall 
        budget control.
      </p>

      <CodeBlock
        code={`# Example: $100/month global cap
Type: Global
Limit: $100
Period: Monthly
Alert at: 80%, 95%`}
        language="text"
      />

      <h3>Provider caps</h3>

      <p>
        Limit spending for a specific provider. Useful if you want to control costs 
        for expensive providers like OpenAI GPT-4.
      </p>

      <CodeBlock
        code={`# Example: $50/month for OpenAI
Type: Provider
Provider: OpenAI
Limit: $50
Period: Monthly`}
        language="text"
      />

      <h3>Model caps</h3>

      <p>
        Limit spending for a specific model. Great for controlling expensive models 
        while allowing cheaper alternatives.
      </p>

      <CodeBlock
        code={`# Example: $20/month for GPT-4o, unlimited for GPT-4o-mini
Type: Model
Model: gpt-4o
Limit: $20
Period: Monthly`}
        language="text"
      />

      <h3>Customer caps</h3>

      <p>
        Limit spending per customer. Essential for SaaS apps to prevent individual 
        customers from running up excessive costs.
      </p>

      <CodeBlock
        code={`# Example: $10/month per customer
Type: Customer
Limit: $10
Period: Monthly
Applies to: All customers (or specific customer IDs)`}
        language="text"
      />

      <h2 id="alerts">Alerts & notifications</h2>

      <p>
        Configure alert thresholds to get notified as spending approaches your cap:
      </p>

      <ul>
        <li><strong>80% alert</strong> — Early warning to review usage</li>
        <li><strong>95% alert</strong> — Urgent warning before cap is hit</li>
        <li><strong>100% alert</strong> — Cap reached notification</li>
      </ul>

      <p>
        Alerts are sent via email to your account email address. Configure additional 
        recipients in Settings → Notifications.
      </p>

      <h2 id="enforcement">Cap enforcement</h2>

      <h3>Soft caps (default)</h3>

      <p>
        By default, caps are soft limits. When exceeded, you receive alerts but API 
        calls continue to work.
      </p>

      <h3>Hard caps</h3>

      <p>
        Enable hard enforcement to actually block API calls when caps are exceeded. 
        The SDK will raise an exception instead of making the LLM call.
      </p>

      <CodeBlock
        code={`from llmobserve import observe
from llmobserve.caps import BudgetExceededError
from openai import OpenAI

observe(api_key="...")
client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
except BudgetExceededError as e:
    # Handle cap exceeded - request was blocked!
    print(f"Spending cap exceeded: {e}")
    for cap in e.exceeded_caps:
        print(f"  - {cap['cap_type']}: {cap['current']}/{cap['limit']}")`}
        language="python"
      />

      <Callout type="info" title="Graceful degradation">
        For hard caps, consider implementing fallback behavior like switching to a 
        cheaper model or queuing the request for later.
      </Callout>

      <h3>Checking cap status programmatically</h3>

      <CodeBlock
        code={`# Check cap status via dashboard API
# Or handle BudgetExceededError in your code

from llmobserve.caps import BudgetExceededError

def make_llm_call(prompt):
    try:
        return client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
    except BudgetExceededError as e:
        # Log the exceeded cap details
        print(f"Cap exceeded: {e.exceeded_caps}")
        # Optionally: switch to cheaper model, queue for later, etc.
        raise`}
        language="python"
      />

      <hr />

      <h3>Next steps</h3>

      <ul>
        <li><Link href="/docs/alerts">Alerts & notifications</Link></li>
        <li><Link href="/docs/customers">Customer tracking</Link></li>
        <li><Link href="/caps">Configure caps in dashboard</Link></li>
      </ul>
    </DocPage>
  );
}


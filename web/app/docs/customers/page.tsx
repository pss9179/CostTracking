"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "why-track-customers", title: "Why track by customer?" },
  { id: "setting-customer-id", title: "Setting customer ID" },
  { id: "dynamic-customer-id", title: "Dynamic customer ID" },
  { id: "viewing-customer-costs", title: "Viewing customer costs" },
  { id: "customer-caps", title: "Customer spending caps" },
];

export default function CustomersPage() {
  return (
    <DocPage
      title="Customer tracking"
      description="Track LLM costs per customer to understand profitability and set usage limits."
      category="Labeling & organization"
      toc={toc}
    >
      <h2 id="why-track-customers">Why track by customer?</h2>

      <p>
        If you're building a SaaS product that uses LLMs, tracking costs per customer helps you:
      </p>

      <ul>
        <li><strong>Understand profitability</strong> — Know which customers cost more than they pay</li>
        <li><strong>Set fair pricing</strong> — Base pricing on actual usage patterns</li>
        <li><strong>Enforce limits</strong> — Set per-customer spending caps</li>
        <li><strong>Identify abuse</strong> — Spot customers with unusually high usage</li>
      </ul>

      <Callout type="tip">
        Customer tracking is completely optional. If you're not running a multi-user application, 
        you can skip this and just track overall costs.
      </Callout>

      <h2 id="setting-customer-id">Setting customer ID</h2>

      <p>
        The simplest way is to pass <code>customer_id</code> when calling <code>observe()</code>:
      </p>

      <CodeBlock
        code={`from llmobserve import observe
from openai import OpenAI

def handle_customer_request(customer_id: str, query: str):
    # Initialize with customer ID
    observe(
        api_key="llmo_sk_...",
        customer_id=customer_id
    )
    
    # All LLM calls are now tracked for this customer
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}]
    )
    
    return response.choices[0].message.content`}
        language="python"
        filename="main.py"
      />

      <h2 id="dynamic-customer-id">Dynamic customer ID</h2>

      <p>
        For web servers where the customer changes per request, use <code>set_customer_id()</code> 
        to dynamically update the customer:
      </p>

      <CodeBlock
        code={`from llmobserve import observe, set_customer_id
from openai import OpenAI
from flask import Flask, request, g

app = Flask(__name__)
client = OpenAI()

# Initialize once at startup
observe(api_key="llmo_sk_...")

@app.before_request
def set_customer():
    # Get customer from auth token, session, etc.
    customer_id = get_customer_from_request(request)
    set_customer_id(customer_id)

@app.route("/chat", methods=["POST"])
def chat():
    # LLM calls are automatically tracked for the current customer
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": request.json["message"]}]
    )
    return {"response": response.choices[0].message.content}`}
        language="python"
        filename="app.py"
      />

      <h3>FastAPI example</h3>

      <CodeBlock
        code={`from llmobserve import observe, set_customer_id
from openai import OpenAI
from fastapi import FastAPI, Depends

app = FastAPI()
client = OpenAI()

observe(api_key="llmo_sk_...")

async def get_current_customer(token: str = Depends(oauth2_scheme)):
    customer = await verify_token(token)
    set_customer_id(customer.id)
    return customer

@app.post("/chat")
async def chat(message: str, customer = Depends(get_current_customer)):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": message}]
    )
    return {"response": response.choices[0].message.content}`}
        language="python"
        filename="app.py"
      />

      <h2 id="viewing-customer-costs">Viewing customer costs</h2>

      <p>
        Once you're tracking by customer, go to the <Link href="/customers">Customers page</Link> in 
        your dashboard to see:
      </p>

      <ul>
        <li><strong>Total cost per customer</strong> — Lifetime and time-filtered</li>
        <li><strong>Call count</strong> — Number of LLM API calls per customer</li>
        <li><strong>Average cost per call</strong> — Helps identify heavy users</li>
        <li><strong>Provider breakdown</strong> — Which models each customer uses</li>
      </ul>

      <h2 id="customer-caps">Customer spending caps</h2>

      <p>
        You can set spending limits per customer to prevent any single customer from 
        running up excessive costs. See <Link href="/docs/spending-caps">Spending caps</Link> for details.
      </p>

      <CodeBlock
        code={`# Example: Check customer usage before processing
from llmobserve import get_customer_usage

usage = get_customer_usage(customer_id)

if usage.total_cost > customer.monthly_limit:
    raise Exception("Customer has exceeded their monthly limit")

# Process request...`}
        language="python"
      />

      <Callout type="info" title="Multi-tenant applications">
        For multi-tenant apps, you can also pass a <code>tenant_id</code> to group customers 
        by tenant. Use <code>tenant_id</code> for the organization and <code>customer_id</code> for 
        individual users within that organization.
      </Callout>

      <hr />

      <h3>Next steps</h3>

      <ul>
        <li><Link href="/docs/spending-caps">Set up spending caps</Link></li>
        <li><Link href="/docs/agents">Agent tracking</Link></li>
        <li><Link href="/docs/sdk">SDK Reference</Link></li>
      </ul>
    </DocPage>
  );
}


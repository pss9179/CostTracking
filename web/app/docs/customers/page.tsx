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
      <h2 id="why-track-customers">How customer tracking works</h2>

      <p>
        <strong>You're building a SaaS that uses LLMs.</strong> Your customers (people who bought your SaaS) 
        make API calls through your app. You want to know: <em>"Which of my customers is costing me the most?"</em>
      </p>

      <p>
        That's what <code>customer_id</code> does. When you set it, every LLM API call gets tagged with that 
        customer's ID. Then in your dashboard, you can see:
      </p>

      <ul>
        <li><strong>Cost per customer</strong> — "Customer A spent $50, Customer B spent $200"</li>
        <li><strong>Profitability</strong> — "Customer B pays $10/month but costs me $200 in API calls"</li>
        <li><strong>Usage patterns</strong> — "Which customers use expensive models vs cheap ones"</li>
        <li><strong>Set limits</strong> — "Block Customer B from spending more than $100/month"</li>
      </ul>

      <Callout type="info" title="Real example">
        <p className="mb-2">
          <strong>Your SaaS:</strong> A chatbot app where users pay $20/month
        </p>
        <p className="mb-2">
          <strong>Your customers:</strong> Alice (user_123), Bob (user_456), Charlie (user_789)
        </p>
        <p>
          <strong>What you see in dashboard:</strong>
        </p>
        <ul className="list-disc ml-6 mt-2">
          <li>user_123: $5.00 (25 calls) — Profitable ✅</li>
          <li>user_456: $150.00 (500 calls) — Losing money ❌</li>
          <li>user_789: $12.00 (60 calls) — Profitable ✅</li>
        </ul>
        <p className="mt-2">
          Now you know: Bob is abusing your service. Set a cap or raise his price.
        </p>
      </Callout>

      <Callout type="tip">
        <strong>Don't have multiple customers?</strong> You can skip customer tracking entirely. 
        Just use <code>observe(api_key="...")</code> without <code>customer_id</code> and track your overall costs.
      </Callout>

      <h2 id="setting-customer-id">Setting customer ID</h2>

      <p>
        <strong>For web apps:</strong> You'll usually set <code>customer_id</code> dynamically per request 
        (see next section). But if you're running a script for a specific customer, you can set it at init:
      </p>

      <CodeBlock
        code={`from llmobserve import observe, set_customer_id
from openai import OpenAI

# Initialize once at startup
observe(api_key="llmo_sk_...")

# When a customer makes a request, set their ID
def handle_customer_request(customer_id: str, query: str):
    # Set customer ID for this request
    set_customer_id(customer_id)
    
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

      <p className="mt-4">
        <strong>Important:</strong> The <code>customer_id</code> is just a string identifier. Use whatever 
        makes sense for your app: user ID, email, Stripe customer ID, etc.
      </p>

      <h2 id="dynamic-customer-id">Dynamic customer ID (recommended for web apps)</h2>

      <p>
        <strong>This is what you'll use 99% of the time.</strong> In a web app, each request comes from 
        a different customer. Set the customer ID at the start of each request, and all LLM calls in that 
        request will be tracked for that customer:
      </p>

      <CodeBlock
        code={`from llmobserve import observe, set_customer_id
from openai import OpenAI
from flask import Flask, request

app = Flask(__name__)
client = OpenAI()

# Initialize once at startup
observe(api_key="llmo_sk_...")

@app.before_request
def set_customer():
    # Get customer ID from your auth system
    # This could be from JWT token, session, database, etc.
    auth_token = request.headers.get("Authorization")
    user = get_user_from_token(auth_token)  # Your auth logic
    
    # Set customer ID - all LLM calls in this request will be tagged
    set_customer_id(user.id)  # or user.email, user.stripe_customer_id, etc.

@app.route("/chat", methods=["POST"])
def chat():
    # This LLM call is automatically tracked for the customer
    # set in @app.before_request
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
from fastapi import FastAPI, Depends, Header

app = FastAPI()
client = OpenAI()

observe(api_key="llmo_sk_...")

async def get_current_customer(authorization: str = Header(...)):
    # Verify JWT token and get user
    user = await verify_jwt_token(authorization)  # Your auth logic
    
    # Set customer ID for this request
    set_customer_id(user.id)  # All LLM calls will be tagged with this
    
    return user

@app.post("/chat")
async def chat(message: str, customer = Depends(get_current_customer)):
    # This LLM call is automatically tracked for the customer
    # set in get_current_customer dependency
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

      <p>
        You can set spending limits per customer in the dashboard. When a customer exceeds their limit, 
        the SDK will raise <code>BudgetExceededError</code> and block the API call. See 
        <Link href="/docs/spending-caps"> Spending caps</Link> for details.
      </p>

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


#!/usr/bin/env node
/**
 * Generate fake test data with multiple customers, providers, and models
 * Sends data directly to the collector API
 */

const COLLECTOR_URL = "https://llmobserve-api-production-d791.up.railway.app";

// Use the API key from test_feature_tracking.py
const API_KEY = process.env.LLMOBSERVE_API_KEY || "llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789";

if (!API_KEY) {
  console.error("Please set LLMOBSERVE_API_KEY environment variable");
  console.log("Get your API key from: https://app.llmobserve.com/settings");
  process.exit(1);
}

const PROVIDERS = ["openai", "anthropic", "mistral", "cohere", "google"];

const MODELS = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  anthropic: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3.5-sonnet"],
  mistral: ["mistral-large", "mistral-medium", "mistral-small"],
  cohere: ["command-r+", "command-r"],
  google: ["gemini-1.5-pro", "gemini-1.5-flash"],
};

const CUSTOMERS = [
  "customer_acme_corp",
  "customer_techstart",
  "customer_enterprise_llc",
  "customer_startup_io",
  "customer_bigdata_inc",
];

const FEATURES = [
  "feature:chat_assistant",
  "feature:document_summary",
  "feature:code_review",
  "feature:email_composer",
  "feature:data_analysis",
];

// Cost per 1k tokens (rough estimates)
const MODEL_COSTS = {
  "gpt-4o": { input: 0.005, output: 0.015 },
  "gpt-4o-mini": { input: 0.00015, output: 0.0006 },
  "gpt-4-turbo": { input: 0.01, output: 0.03 },
  "gpt-3.5-turbo": { input: 0.0005, output: 0.0015 },
  "claude-3-opus": { input: 0.015, output: 0.075 },
  "claude-3-sonnet": { input: 0.003, output: 0.015 },
  "claude-3-haiku": { input: 0.00025, output: 0.00125 },
  "claude-3.5-sonnet": { input: 0.003, output: 0.015 },
  "mistral-large": { input: 0.004, output: 0.012 },
  "mistral-medium": { input: 0.0027, output: 0.0081 },
  "mistral-small": { input: 0.001, output: 0.003 },
  "command-r+": { input: 0.003, output: 0.015 },
  "command-r": { input: 0.0005, output: 0.0015 },
  "gemini-1.5-pro": { input: 0.00125, output: 0.005 },
  "gemini-1.5-flash": { input: 0.000075, output: 0.0003 },
};

function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function generateEvent(hoursAgo) {
  const provider = randomChoice(PROVIDERS);
  const model = randomChoice(MODELS[provider]);
  const customer = randomChoice(CUSTOMERS);
  const feature = randomChoice(FEATURES);
  
  const inputTokens = randomInt(100, 2000);
  const outputTokens = randomInt(50, 1000);
  const costs = MODEL_COSTS[model] || { input: 0.001, output: 0.002 };
  const cost = (inputTokens * costs.input + outputTokens * costs.output) / 1000;
  
  const latency = randomInt(200, 5000);
  
  // Create timestamp for hoursAgo
  const timestamp = new Date(Date.now() - hoursAgo * 60 * 60 * 1000);
  // Add some random minutes within the hour
  timestamp.setMinutes(randomInt(0, 59));
  timestamp.setSeconds(randomInt(0, 59));
  
  const id = `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const run_id = `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const span_id = `span_${Math.random().toString(36).substr(2, 9)}`;
  
  return {
    id,
    run_id,
    span_id,
    section: feature,
    span_type: "llm",
    provider,
    endpoint: "chat.completions",
    model,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    cost_usd: cost,
    latency_ms: latency,
    status: "success",
    customer_id: customer,
    semantic_label: feature,
  };
}

async function sendEvent(event) {
  const response = await fetch(`${COLLECTOR_URL}/events/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${API_KEY}`,
    },
    body: JSON.stringify([event]),
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to send event: ${response.status} - ${text}`);
  }
  
  return response.json();
}

async function main() {
  console.log("🚀 Generating fake test data...\n");
  
  // Generate events spread across different time periods
  const timeDistribution = [
    { hoursAgo: 0.5, count: 10, label: "Last 30 minutes" },
    { hoursAgo: 2, count: 15, label: "2 hours ago" },
    { hoursAgo: 6, count: 20, label: "6 hours ago" },
    { hoursAgo: 12, count: 25, label: "12 hours ago" },
    { hoursAgo: 24, count: 20, label: "24 hours ago" },
    { hoursAgo: 48, count: 15, label: "2 days ago" },
    { hoursAgo: 72, count: 10, label: "3 days ago" },
    { hoursAgo: 120, count: 10, label: "5 days ago" },
  ];
  
  let totalEvents = 0;
  let totalCost = 0;
  
  for (const period of timeDistribution) {
    console.log(`📊 Generating ${period.count} events for ${period.label}...`);
    
    for (let i = 0; i < period.count; i++) {
      // Add some randomness to the exact time within the period
      const hoursAgo = period.hoursAgo + (Math.random() - 0.5) * 2;
      const event = generateEvent(Math.max(0, hoursAgo));
      
      try {
        await sendEvent(event);
        totalEvents++;
        totalCost += event.cost_usd;
        process.stdout.write(".");
      } catch (error) {
        console.error(`\n❌ Error: ${error.message}`);
      }
    }
    console.log(" ✅");
  }
  
  console.log(`\n✨ Done! Generated ${totalEvents} events`);
  console.log(`💰 Total cost: $${totalCost.toFixed(4)}`);
  console.log(`\n📈 Customer breakdown:`);
  console.log(`   - ${CUSTOMERS.join("\n   - ")}`);
  console.log(`\n🔧 Features tracked:`);
  console.log(`   - ${FEATURES.join("\n   - ")}`);
  console.log(`\n🔄 Refresh your dashboard to see the data!`);
}

main().catch(console.error);

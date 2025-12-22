// Generate test data directly to the collector API
// This simulates multiple providers and models for testing the dashboard

const COLLECTOR_URL = 'https://llmobserve-api-production-d791.up.railway.app';
const API_KEY = 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789';

// Test data configuration - multiple providers and models
const testData = [
  // OpenAI models
  { provider: 'openai', model: 'gpt-4o', inputTokens: 50, outputTokens: 100, inputCost: 0.00025, outputCost: 0.001 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 80, outputTokens: 150, inputCost: 0.0004, outputCost: 0.0015 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 30, outputTokens: 80, inputCost: 0.00015, outputCost: 0.0008 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 100, outputTokens: 200, inputCost: 0.00015, outputCost: 0.0006 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 150, outputTokens: 300, inputCost: 0.000225, outputCost: 0.0009 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 60, outputTokens: 120, inputCost: 0.0006, outputCost: 0.0036 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 40, outputTokens: 90, inputCost: 0.0004, outputCost: 0.0027 },
  { provider: 'openai', model: 'gpt-4', inputTokens: 50, outputTokens: 100, inputCost: 0.0015, outputCost: 0.006 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 80, outputTokens: 150, inputCost: 0.00004, outputCost: 0.00009 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 120, outputTokens: 250, inputCost: 0.00006, outputCost: 0.000125 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 60, outputTokens: 100, inputCost: 0.00003, outputCost: 0.00005 },
  
  // Anthropic models
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 100, outputTokens: 200, inputCost: 0.0015, outputCost: 0.0075 },
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 80, outputTokens: 150, inputCost: 0.0012, outputCost: 0.005625 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 150, outputTokens: 300, inputCost: 0.00045, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 100, outputTokens: 250, inputCost: 0.0003, outputCost: 0.00375 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 200, outputTokens: 400, inputCost: 0.0006, outputCost: 0.006 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 120, outputTokens: 300, inputCost: 0.00036, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 300, outputTokens: 500, inputCost: 0.000075, outputCost: 0.000625 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 200, outputTokens: 400, inputCost: 0.00005, outputCost: 0.0005 },
  
  // Google models
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 100, outputTokens: 200, inputCost: 0.000125, outputCost: 0.0005 },
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 150, outputTokens: 300, inputCost: 0.0001875, outputCost: 0.00075 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 200, outputTokens: 400, inputCost: 0.00001, outputCost: 0.00003 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 300, outputTokens: 500, inputCost: 0.000015, outputCost: 0.0000375 },
  
  // Mistral models
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 100, outputTokens: 200, inputCost: 0.0002, outputCost: 0.0006 },
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 80, outputTokens: 150, inputCost: 0.00016, outputCost: 0.00045 },
  { provider: 'mistral', model: 'mistral-medium', inputTokens: 150, outputTokens: 300, inputCost: 0.000405, outputCost: 0.00243 },
  { provider: 'mistral', model: 'mistral-small-latest', inputTokens: 200, outputTokens: 400, inputCost: 0.0002, outputCost: 0.0006 },
  
  // Cohere models
  { provider: 'cohere', model: 'command-r-plus', inputTokens: 100, outputTokens: 200, inputCost: 0.0003, outputCost: 0.0015 },
  { provider: 'cohere', model: 'command-r', inputTokens: 150, outputTokens: 300, inputCost: 0.000075, outputCost: 0.00045 },
];

// Generate a unique UUID
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function sendEvents(events, batchNum) {
  // Convert to TraceEventCreate format
  const formattedEvents = events.map((data, i) => {
    const cost = (data.inputCost || 0) + (data.outputCost || 0);
    const runId = generateUUID();
    const spanId = generateUUID();
    
    return {
      id: generateUUID(),
      run_id: runId,
      span_id: spanId,
      parent_span_id: null,
      section: 'main',
      section_path: 'main',
      span_type: 'llm_call',
      provider: data.provider,
      endpoint: 'chat/completions',
      model: data.model,
      tenant_id: 'default_tenant',
      customer_id: null,
      input_tokens: data.inputTokens,
      output_tokens: data.outputTokens,
      cached_tokens: 0,
      cost_usd: cost,
      latency_ms: Math.floor(Math.random() * 2000) + 500,
      status: 'ok',
      is_streaming: false,
      stream_cancelled: false,
      event_metadata: {},
      semantic_label: null,
    };
  });

  try {
    const response = await fetch(`${COLLECTOR_URL}/events/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(formattedEvents),
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`[Batch ${batchNum}] ✅ Created: ${result.created}, Skipped: ${result.skipped}`);
      return result.created;
    } else {
      const errorText = await response.text();
      console.log(`[Batch ${batchNum}] ❌ Error: ${response.status} - ${errorText.substring(0, 200)}`);
      return 0;
    }
  } catch (error) {
    console.log(`[Batch ${batchNum}] ❌ Network error: ${error.message}`);
    return 0;
  }
}

async function main() {
  console.log('🚀 Generating test data for LLMObserve dashboard...\n');
  console.log('='.repeat(70));
  console.log(`Collector: ${COLLECTOR_URL}`);
  console.log(`Total events: ${testData.length}`);
  console.log('='.repeat(70) + '\n');

  // Send in batches of 10
  const batchSize = 10;
  let totalCreated = 0;
  let batchNum = 1;

  for (let i = 0; i < testData.length; i += batchSize) {
    const batch = testData.slice(i, i + batchSize);
    console.log(`\n📦 Sending batch ${batchNum} (${batch.length} events)...`);
    
    // Log what's in the batch
    const providers = [...new Set(batch.map(d => d.provider))];
    console.log(`   Providers: ${providers.join(', ')}`);
    
    const created = await sendEvents(batch, batchNum);
    totalCreated += created;
    batchNum++;
    
    // Small delay between batches
    await new Promise(r => setTimeout(r, 300));
  }

  console.log('\n' + '='.repeat(70));
  
  // Calculate totals by provider
  const providerTotals = {};
  const modelCounts = {};
  testData.forEach(d => {
    const cost = (d.inputCost || 0) + (d.outputCost || 0);
    providerTotals[d.provider] = (providerTotals[d.provider] || 0) + cost;
    modelCounts[d.model] = (modelCounts[d.model] || 0) + 1;
  });
  
  console.log(`\n📊 Summary:`);
  console.log(`   Total events sent: ${testData.length}`);
  console.log(`   Successfully created: ${totalCreated}`);
  
  console.log(`\n📈 Expected costs by provider:`);
  Object.entries(providerTotals).sort((a, b) => b[1] - a[1]).forEach(([provider, cost]) => {
    console.log(`   ${provider}: $${cost.toFixed(6)}`);
  });
  
  console.log(`\n🔢 Events by model:`);
  Object.entries(modelCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).forEach(([model, count]) => {
    console.log(`   ${model}: ${count}`);
  });
  
  console.log('\n✅ Data generation complete!');
  console.log('🔗 Check dashboard: https://app.llmobserve.com/dashboard\n');
}

main().catch(console.error);


const COLLECTOR_URL = 'https://llmobserve-api-production-d791.up.railway.app';
const API_KEY = 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789';

// Test data configuration - multiple providers and models
const testData = [
  // OpenAI models
  { provider: 'openai', model: 'gpt-4o', inputTokens: 50, outputTokens: 100, inputCost: 0.00025, outputCost: 0.001 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 80, outputTokens: 150, inputCost: 0.0004, outputCost: 0.0015 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 30, outputTokens: 80, inputCost: 0.00015, outputCost: 0.0008 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 100, outputTokens: 200, inputCost: 0.00015, outputCost: 0.0006 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 150, outputTokens: 300, inputCost: 0.000225, outputCost: 0.0009 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 60, outputTokens: 120, inputCost: 0.0006, outputCost: 0.0036 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 40, outputTokens: 90, inputCost: 0.0004, outputCost: 0.0027 },
  { provider: 'openai', model: 'gpt-4', inputTokens: 50, outputTokens: 100, inputCost: 0.0015, outputCost: 0.006 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 80, outputTokens: 150, inputCost: 0.00004, outputCost: 0.00009 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 120, outputTokens: 250, inputCost: 0.00006, outputCost: 0.000125 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 60, outputTokens: 100, inputCost: 0.00003, outputCost: 0.00005 },
  
  // Anthropic models
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 100, outputTokens: 200, inputCost: 0.0015, outputCost: 0.0075 },
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 80, outputTokens: 150, inputCost: 0.0012, outputCost: 0.005625 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 150, outputTokens: 300, inputCost: 0.00045, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 100, outputTokens: 250, inputCost: 0.0003, outputCost: 0.00375 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 200, outputTokens: 400, inputCost: 0.0006, outputCost: 0.006 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 120, outputTokens: 300, inputCost: 0.00036, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 300, outputTokens: 500, inputCost: 0.000075, outputCost: 0.000625 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 200, outputTokens: 400, inputCost: 0.00005, outputCost: 0.0005 },
  
  // Google models
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 100, outputTokens: 200, inputCost: 0.000125, outputCost: 0.0005 },
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 150, outputTokens: 300, inputCost: 0.0001875, outputCost: 0.00075 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 200, outputTokens: 400, inputCost: 0.00001, outputCost: 0.00003 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 300, outputTokens: 500, inputCost: 0.000015, outputCost: 0.0000375 },
  
  // Mistral models
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 100, outputTokens: 200, inputCost: 0.0002, outputCost: 0.0006 },
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 80, outputTokens: 150, inputCost: 0.00016, outputCost: 0.00045 },
  { provider: 'mistral', model: 'mistral-medium', inputTokens: 150, outputTokens: 300, inputCost: 0.000405, outputCost: 0.00243 },
  { provider: 'mistral', model: 'mistral-small-latest', inputTokens: 200, outputTokens: 400, inputCost: 0.0002, outputCost: 0.0006 },
  
  // Cohere models
  { provider: 'cohere', model: 'command-r-plus', inputTokens: 100, outputTokens: 200, inputCost: 0.0003, outputCost: 0.0015 },
  { provider: 'cohere', model: 'command-r', inputTokens: 150, outputTokens: 300, inputCost: 0.000075, outputCost: 0.00045 },
];

// Generate a unique UUID
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function sendEvents(events, batchNum) {
  // Convert to TraceEventCreate format
  const formattedEvents = events.map((data, i) => {
    const cost = (data.inputCost || 0) + (data.outputCost || 0);
    const runId = generateUUID();
    const spanId = generateUUID();
    
    return {
      id: generateUUID(),
      run_id: runId,
      span_id: spanId,
      parent_span_id: null,
      section: 'main',
      section_path: 'main',
      span_type: 'llm_call',
      provider: data.provider,
      endpoint: 'chat/completions',
      model: data.model,
      tenant_id: 'default_tenant',
      customer_id: null,
      input_tokens: data.inputTokens,
      output_tokens: data.outputTokens,
      cached_tokens: 0,
      cost_usd: cost,
      latency_ms: Math.floor(Math.random() * 2000) + 500,
      status: 'ok',
      is_streaming: false,
      stream_cancelled: false,
      event_metadata: {},
      semantic_label: null,
    };
  });

  try {
    const response = await fetch(`${COLLECTOR_URL}/events/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(formattedEvents),
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`[Batch ${batchNum}] ✅ Created: ${result.created}, Skipped: ${result.skipped}`);
      return result.created;
    } else {
      const errorText = await response.text();
      console.log(`[Batch ${batchNum}] ❌ Error: ${response.status} - ${errorText.substring(0, 200)}`);
      return 0;
    }
  } catch (error) {
    console.log(`[Batch ${batchNum}] ❌ Network error: ${error.message}`);
    return 0;
  }
}

async function main() {
  console.log('🚀 Generating test data for LLMObserve dashboard...\n');
  console.log('='.repeat(70));
  console.log(`Collector: ${COLLECTOR_URL}`);
  console.log(`Total events: ${testData.length}`);
  console.log('='.repeat(70) + '\n');

  // Send in batches of 10
  const batchSize = 10;
  let totalCreated = 0;
  let batchNum = 1;

  for (let i = 0; i < testData.length; i += batchSize) {
    const batch = testData.slice(i, i + batchSize);
    console.log(`\n📦 Sending batch ${batchNum} (${batch.length} events)...`);
    
    // Log what's in the batch
    const providers = [...new Set(batch.map(d => d.provider))];
    console.log(`   Providers: ${providers.join(', ')}`);
    
    const created = await sendEvents(batch, batchNum);
    totalCreated += created;
    batchNum++;
    
    // Small delay between batches
    await new Promise(r => setTimeout(r, 300));
  }

  console.log('\n' + '='.repeat(70));
  
  // Calculate totals by provider
  const providerTotals = {};
  const modelCounts = {};
  testData.forEach(d => {
    const cost = (d.inputCost || 0) + (d.outputCost || 0);
    providerTotals[d.provider] = (providerTotals[d.provider] || 0) + cost;
    modelCounts[d.model] = (modelCounts[d.model] || 0) + 1;
  });
  
  console.log(`\n📊 Summary:`);
  console.log(`   Total events sent: ${testData.length}`);
  console.log(`   Successfully created: ${totalCreated}`);
  
  console.log(`\n📈 Expected costs by provider:`);
  Object.entries(providerTotals).sort((a, b) => b[1] - a[1]).forEach(([provider, cost]) => {
    console.log(`   ${provider}: $${cost.toFixed(6)}`);
  });
  
  console.log(`\n🔢 Events by model:`);
  Object.entries(modelCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).forEach(([model, count]) => {
    console.log(`   ${model}: ${count}`);
  });
  
  console.log('\n✅ Data generation complete!');
  console.log('🔗 Check dashboard: https://app.llmobserve.com/dashboard\n');
}

main().catch(console.error);


const COLLECTOR_URL = 'https://llmobserve-api-production-d791.up.railway.app';
const API_KEY = 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789';

// Test data configuration - multiple providers and models
const testData = [
  // OpenAI models
  { provider: 'openai', model: 'gpt-4o', inputTokens: 50, outputTokens: 100, inputCost: 0.00025, outputCost: 0.001 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 80, outputTokens: 150, inputCost: 0.0004, outputCost: 0.0015 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 30, outputTokens: 80, inputCost: 0.00015, outputCost: 0.0008 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 100, outputTokens: 200, inputCost: 0.00015, outputCost: 0.0006 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 150, outputTokens: 300, inputCost: 0.000225, outputCost: 0.0009 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 60, outputTokens: 120, inputCost: 0.0006, outputCost: 0.0036 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 40, outputTokens: 90, inputCost: 0.0004, outputCost: 0.0027 },
  { provider: 'openai', model: 'gpt-4', inputTokens: 50, outputTokens: 100, inputCost: 0.0015, outputCost: 0.006 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 80, outputTokens: 150, inputCost: 0.00004, outputCost: 0.00009 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 120, outputTokens: 250, inputCost: 0.00006, outputCost: 0.000125 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 60, outputTokens: 100, inputCost: 0.00003, outputCost: 0.00005 },
  
  // Anthropic models
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 100, outputTokens: 200, inputCost: 0.0015, outputCost: 0.0075 },
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 80, outputTokens: 150, inputCost: 0.0012, outputCost: 0.005625 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 150, outputTokens: 300, inputCost: 0.00045, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 100, outputTokens: 250, inputCost: 0.0003, outputCost: 0.00375 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 200, outputTokens: 400, inputCost: 0.0006, outputCost: 0.006 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 120, outputTokens: 300, inputCost: 0.00036, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 300, outputTokens: 500, inputCost: 0.000075, outputCost: 0.000625 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 200, outputTokens: 400, inputCost: 0.00005, outputCost: 0.0005 },
  
  // Google models
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 100, outputTokens: 200, inputCost: 0.000125, outputCost: 0.0005 },
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 150, outputTokens: 300, inputCost: 0.0001875, outputCost: 0.00075 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 200, outputTokens: 400, inputCost: 0.00001, outputCost: 0.00003 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 300, outputTokens: 500, inputCost: 0.000015, outputCost: 0.0000375 },
  
  // Mistral models
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 100, outputTokens: 200, inputCost: 0.0002, outputCost: 0.0006 },
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 80, outputTokens: 150, inputCost: 0.00016, outputCost: 0.00045 },
  { provider: 'mistral', model: 'mistral-medium', inputTokens: 150, outputTokens: 300, inputCost: 0.000405, outputCost: 0.00243 },
  { provider: 'mistral', model: 'mistral-small-latest', inputTokens: 200, outputTokens: 400, inputCost: 0.0002, outputCost: 0.0006 },
  
  // Cohere models
  { provider: 'cohere', model: 'command-r-plus', inputTokens: 100, outputTokens: 200, inputCost: 0.0003, outputCost: 0.0015 },
  { provider: 'cohere', model: 'command-r', inputTokens: 150, outputTokens: 300, inputCost: 0.000075, outputCost: 0.00045 },
];

// Generate a unique UUID
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function sendEvents(events, batchNum) {
  // Convert to TraceEventCreate format
  const formattedEvents = events.map((data, i) => {
    const cost = (data.inputCost || 0) + (data.outputCost || 0);
    const runId = generateUUID();
    const spanId = generateUUID();
    
    return {
      id: generateUUID(),
      run_id: runId,
      span_id: spanId,
      parent_span_id: null,
      section: 'main',
      section_path: 'main',
      span_type: 'llm_call',
      provider: data.provider,
      endpoint: 'chat/completions',
      model: data.model,
      tenant_id: 'default_tenant',
      customer_id: null,
      input_tokens: data.inputTokens,
      output_tokens: data.outputTokens,
      cached_tokens: 0,
      cost_usd: cost,
      latency_ms: Math.floor(Math.random() * 2000) + 500,
      status: 'ok',
      is_streaming: false,
      stream_cancelled: false,
      event_metadata: {},
      semantic_label: null,
    };
  });

  try {
    const response = await fetch(`${COLLECTOR_URL}/events/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(formattedEvents),
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`[Batch ${batchNum}] ✅ Created: ${result.created}, Skipped: ${result.skipped}`);
      return result.created;
    } else {
      const errorText = await response.text();
      console.log(`[Batch ${batchNum}] ❌ Error: ${response.status} - ${errorText.substring(0, 200)}`);
      return 0;
    }
  } catch (error) {
    console.log(`[Batch ${batchNum}] ❌ Network error: ${error.message}`);
    return 0;
  }
}

async function main() {
  console.log('🚀 Generating test data for LLMObserve dashboard...\n');
  console.log('='.repeat(70));
  console.log(`Collector: ${COLLECTOR_URL}`);
  console.log(`Total events: ${testData.length}`);
  console.log('='.repeat(70) + '\n');

  // Send in batches of 10
  const batchSize = 10;
  let totalCreated = 0;
  let batchNum = 1;

  for (let i = 0; i < testData.length; i += batchSize) {
    const batch = testData.slice(i, i + batchSize);
    console.log(`\n📦 Sending batch ${batchNum} (${batch.length} events)...`);
    
    // Log what's in the batch
    const providers = [...new Set(batch.map(d => d.provider))];
    console.log(`   Providers: ${providers.join(', ')}`);
    
    const created = await sendEvents(batch, batchNum);
    totalCreated += created;
    batchNum++;
    
    // Small delay between batches
    await new Promise(r => setTimeout(r, 300));
  }

  console.log('\n' + '='.repeat(70));
  
  // Calculate totals by provider
  const providerTotals = {};
  const modelCounts = {};
  testData.forEach(d => {
    const cost = (d.inputCost || 0) + (d.outputCost || 0);
    providerTotals[d.provider] = (providerTotals[d.provider] || 0) + cost;
    modelCounts[d.model] = (modelCounts[d.model] || 0) + 1;
  });
  
  console.log(`\n📊 Summary:`);
  console.log(`   Total events sent: ${testData.length}`);
  console.log(`   Successfully created: ${totalCreated}`);
  
  console.log(`\n📈 Expected costs by provider:`);
  Object.entries(providerTotals).sort((a, b) => b[1] - a[1]).forEach(([provider, cost]) => {
    console.log(`   ${provider}: $${cost.toFixed(6)}`);
  });
  
  console.log(`\n🔢 Events by model:`);
  Object.entries(modelCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).forEach(([model, count]) => {
    console.log(`   ${model}: ${count}`);
  });
  
  console.log('\n✅ Data generation complete!');
  console.log('🔗 Check dashboard: https://app.llmobserve.com/dashboard\n');
}

main().catch(console.error);


const COLLECTOR_URL = 'https://llmobserve-api-production-d791.up.railway.app';
const API_KEY = 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789';

// Test data configuration - multiple providers and models
const testData = [
  // OpenAI models
  { provider: 'openai', model: 'gpt-4o', inputTokens: 50, outputTokens: 100, inputCost: 0.00025, outputCost: 0.001 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 80, outputTokens: 150, inputCost: 0.0004, outputCost: 0.0015 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 30, outputTokens: 80, inputCost: 0.00015, outputCost: 0.0008 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 100, outputTokens: 200, inputCost: 0.00015, outputCost: 0.0006 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 150, outputTokens: 300, inputCost: 0.000225, outputCost: 0.0009 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 60, outputTokens: 120, inputCost: 0.0006, outputCost: 0.0036 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 40, outputTokens: 90, inputCost: 0.0004, outputCost: 0.0027 },
  { provider: 'openai', model: 'gpt-4', inputTokens: 50, outputTokens: 100, inputCost: 0.0015, outputCost: 0.006 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 80, outputTokens: 150, inputCost: 0.00004, outputCost: 0.00009 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 120, outputTokens: 250, inputCost: 0.00006, outputCost: 0.000125 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 60, outputTokens: 100, inputCost: 0.00003, outputCost: 0.00005 },
  
  // Anthropic models
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 100, outputTokens: 200, inputCost: 0.0015, outputCost: 0.0075 },
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 80, outputTokens: 150, inputCost: 0.0012, outputCost: 0.005625 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 150, outputTokens: 300, inputCost: 0.00045, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 100, outputTokens: 250, inputCost: 0.0003, outputCost: 0.00375 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 200, outputTokens: 400, inputCost: 0.0006, outputCost: 0.006 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 120, outputTokens: 300, inputCost: 0.00036, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 300, outputTokens: 500, inputCost: 0.000075, outputCost: 0.000625 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 200, outputTokens: 400, inputCost: 0.00005, outputCost: 0.0005 },
  
  // Google models
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 100, outputTokens: 200, inputCost: 0.000125, outputCost: 0.0005 },
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 150, outputTokens: 300, inputCost: 0.0001875, outputCost: 0.00075 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 200, outputTokens: 400, inputCost: 0.00001, outputCost: 0.00003 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 300, outputTokens: 500, inputCost: 0.000015, outputCost: 0.0000375 },
  
  // Mistral models
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 100, outputTokens: 200, inputCost: 0.0002, outputCost: 0.0006 },
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 80, outputTokens: 150, inputCost: 0.00016, outputCost: 0.00045 },
  { provider: 'mistral', model: 'mistral-medium', inputTokens: 150, outputTokens: 300, inputCost: 0.000405, outputCost: 0.00243 },
  { provider: 'mistral', model: 'mistral-small-latest', inputTokens: 200, outputTokens: 400, inputCost: 0.0002, outputCost: 0.0006 },
  
  // Cohere models
  { provider: 'cohere', model: 'command-r-plus', inputTokens: 100, outputTokens: 200, inputCost: 0.0003, outputCost: 0.0015 },
  { provider: 'cohere', model: 'command-r', inputTokens: 150, outputTokens: 300, inputCost: 0.000075, outputCost: 0.00045 },
];

// Generate a unique UUID
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function sendEvents(events, batchNum) {
  // Convert to TraceEventCreate format
  const formattedEvents = events.map((data, i) => {
    const cost = (data.inputCost || 0) + (data.outputCost || 0);
    const runId = generateUUID();
    const spanId = generateUUID();
    
    return {
      id: generateUUID(),
      run_id: runId,
      span_id: spanId,
      parent_span_id: null,
      section: 'main',
      section_path: 'main',
      span_type: 'llm_call',
      provider: data.provider,
      endpoint: 'chat/completions',
      model: data.model,
      tenant_id: 'default_tenant',
      customer_id: null,
      input_tokens: data.inputTokens,
      output_tokens: data.outputTokens,
      cached_tokens: 0,
      cost_usd: cost,
      latency_ms: Math.floor(Math.random() * 2000) + 500,
      status: 'ok',
      is_streaming: false,
      stream_cancelled: false,
      event_metadata: {},
      semantic_label: null,
    };
  });

  try {
    const response = await fetch(`${COLLECTOR_URL}/events/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(formattedEvents),
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`[Batch ${batchNum}] ✅ Created: ${result.created}, Skipped: ${result.skipped}`);
      return result.created;
    } else {
      const errorText = await response.text();
      console.log(`[Batch ${batchNum}] ❌ Error: ${response.status} - ${errorText.substring(0, 200)}`);
      return 0;
    }
  } catch (error) {
    console.log(`[Batch ${batchNum}] ❌ Network error: ${error.message}`);
    return 0;
  }
}

async function main() {
  console.log('🚀 Generating test data for LLMObserve dashboard...\n');
  console.log('='.repeat(70));
  console.log(`Collector: ${COLLECTOR_URL}`);
  console.log(`Total events: ${testData.length}`);
  console.log('='.repeat(70) + '\n');

  // Send in batches of 10
  const batchSize = 10;
  let totalCreated = 0;
  let batchNum = 1;

  for (let i = 0; i < testData.length; i += batchSize) {
    const batch = testData.slice(i, i + batchSize);
    console.log(`\n📦 Sending batch ${batchNum} (${batch.length} events)...`);
    
    // Log what's in the batch
    const providers = [...new Set(batch.map(d => d.provider))];
    console.log(`   Providers: ${providers.join(', ')}`);
    
    const created = await sendEvents(batch, batchNum);
    totalCreated += created;
    batchNum++;
    
    // Small delay between batches
    await new Promise(r => setTimeout(r, 300));
  }

  console.log('\n' + '='.repeat(70));
  
  // Calculate totals by provider
  const providerTotals = {};
  const modelCounts = {};
  testData.forEach(d => {
    const cost = (d.inputCost || 0) + (d.outputCost || 0);
    providerTotals[d.provider] = (providerTotals[d.provider] || 0) + cost;
    modelCounts[d.model] = (modelCounts[d.model] || 0) + 1;
  });
  
  console.log(`\n📊 Summary:`);
  console.log(`   Total events sent: ${testData.length}`);
  console.log(`   Successfully created: ${totalCreated}`);
  
  console.log(`\n📈 Expected costs by provider:`);
  Object.entries(providerTotals).sort((a, b) => b[1] - a[1]).forEach(([provider, cost]) => {
    console.log(`   ${provider}: $${cost.toFixed(6)}`);
  });
  
  console.log(`\n🔢 Events by model:`);
  Object.entries(modelCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).forEach(([model, count]) => {
    console.log(`   ${model}: ${count}`);
  });
  
  console.log('\n✅ Data generation complete!');
  console.log('🔗 Check dashboard: https://app.llmobserve.com/dashboard\n');
}

main().catch(console.error);


const COLLECTOR_URL = 'https://llmobserve-api-production-d791.up.railway.app';
const API_KEY = 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789';

// Test data configuration - multiple providers and models
const testData = [
  // OpenAI models
  { provider: 'openai', model: 'gpt-4o', inputTokens: 50, outputTokens: 100, inputCost: 0.00025, outputCost: 0.001 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 80, outputTokens: 150, inputCost: 0.0004, outputCost: 0.0015 },
  { provider: 'openai', model: 'gpt-4o', inputTokens: 30, outputTokens: 80, inputCost: 0.00015, outputCost: 0.0008 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 100, outputTokens: 200, inputCost: 0.00015, outputCost: 0.0006 },
  { provider: 'openai', model: 'gpt-4o-mini', inputTokens: 150, outputTokens: 300, inputCost: 0.000225, outputCost: 0.0009 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 60, outputTokens: 120, inputCost: 0.0006, outputCost: 0.0036 },
  { provider: 'openai', model: 'gpt-4-turbo', inputTokens: 40, outputTokens: 90, inputCost: 0.0004, outputCost: 0.0027 },
  { provider: 'openai', model: 'gpt-4', inputTokens: 50, outputTokens: 100, inputCost: 0.0015, outputCost: 0.006 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 80, outputTokens: 150, inputCost: 0.00004, outputCost: 0.00009 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 120, outputTokens: 250, inputCost: 0.00006, outputCost: 0.000125 },
  { provider: 'openai', model: 'gpt-3.5-turbo', inputTokens: 60, outputTokens: 100, inputCost: 0.00003, outputCost: 0.00005 },
  
  // Anthropic models
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 100, outputTokens: 200, inputCost: 0.0015, outputCost: 0.0075 },
  { provider: 'anthropic', model: 'claude-3-opus-20240229', inputTokens: 80, outputTokens: 150, inputCost: 0.0012, outputCost: 0.005625 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 150, outputTokens: 300, inputCost: 0.00045, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-sonnet-20240229', inputTokens: 100, outputTokens: 250, inputCost: 0.0003, outputCost: 0.00375 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 200, outputTokens: 400, inputCost: 0.0006, outputCost: 0.006 },
  { provider: 'anthropic', model: 'claude-3-5-sonnet-20241022', inputTokens: 120, outputTokens: 300, inputCost: 0.00036, outputCost: 0.0045 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 300, outputTokens: 500, inputCost: 0.000075, outputCost: 0.000625 },
  { provider: 'anthropic', model: 'claude-3-haiku-20240307', inputTokens: 200, outputTokens: 400, inputCost: 0.00005, outputCost: 0.0005 },
  
  // Google models
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 100, outputTokens: 200, inputCost: 0.000125, outputCost: 0.0005 },
  { provider: 'google', model: 'gemini-1.5-pro', inputTokens: 150, outputTokens: 300, inputCost: 0.0001875, outputCost: 0.00075 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 200, outputTokens: 400, inputCost: 0.00001, outputCost: 0.00003 },
  { provider: 'google', model: 'gemini-1.5-flash', inputTokens: 300, outputTokens: 500, inputCost: 0.000015, outputCost: 0.0000375 },
  
  // Mistral models
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 100, outputTokens: 200, inputCost: 0.0002, outputCost: 0.0006 },
  { provider: 'mistral', model: 'mistral-large-latest', inputTokens: 80, outputTokens: 150, inputCost: 0.00016, outputCost: 0.00045 },
  { provider: 'mistral', model: 'mistral-medium', inputTokens: 150, outputTokens: 300, inputCost: 0.000405, outputCost: 0.00243 },
  { provider: 'mistral', model: 'mistral-small-latest', inputTokens: 200, outputTokens: 400, inputCost: 0.0002, outputCost: 0.0006 },
  
  // Cohere models
  { provider: 'cohere', model: 'command-r-plus', inputTokens: 100, outputTokens: 200, inputCost: 0.0003, outputCost: 0.0015 },
  { provider: 'cohere', model: 'command-r', inputTokens: 150, outputTokens: 300, inputCost: 0.000075, outputCost: 0.00045 },
];

// Generate a unique UUID
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function sendEvents(events, batchNum) {
  // Convert to TraceEventCreate format
  const formattedEvents = events.map((data, i) => {
    const cost = (data.inputCost || 0) + (data.outputCost || 0);
    const runId = generateUUID();
    const spanId = generateUUID();
    
    return {
      id: generateUUID(),
      run_id: runId,
      span_id: spanId,
      parent_span_id: null,
      section: 'main',
      section_path: 'main',
      span_type: 'llm_call',
      provider: data.provider,
      endpoint: 'chat/completions',
      model: data.model,
      tenant_id: 'default_tenant',
      customer_id: null,
      input_tokens: data.inputTokens,
      output_tokens: data.outputTokens,
      cached_tokens: 0,
      cost_usd: cost,
      latency_ms: Math.floor(Math.random() * 2000) + 500,
      status: 'ok',
      is_streaming: false,
      stream_cancelled: false,
      event_metadata: {},
      semantic_label: null,
    };
  });

  try {
    const response = await fetch(`${COLLECTOR_URL}/events/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(formattedEvents),
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`[Batch ${batchNum}] ✅ Created: ${result.created}, Skipped: ${result.skipped}`);
      return result.created;
    } else {
      const errorText = await response.text();
      console.log(`[Batch ${batchNum}] ❌ Error: ${response.status} - ${errorText.substring(0, 200)}`);
      return 0;
    }
  } catch (error) {
    console.log(`[Batch ${batchNum}] ❌ Network error: ${error.message}`);
    return 0;
  }
}

async function main() {
  console.log('🚀 Generating test data for LLMObserve dashboard...\n');
  console.log('='.repeat(70));
  console.log(`Collector: ${COLLECTOR_URL}`);
  console.log(`Total events: ${testData.length}`);
  console.log('='.repeat(70) + '\n');

  // Send in batches of 10
  const batchSize = 10;
  let totalCreated = 0;
  let batchNum = 1;

  for (let i = 0; i < testData.length; i += batchSize) {
    const batch = testData.slice(i, i + batchSize);
    console.log(`\n📦 Sending batch ${batchNum} (${batch.length} events)...`);
    
    // Log what's in the batch
    const providers = [...new Set(batch.map(d => d.provider))];
    console.log(`   Providers: ${providers.join(', ')}`);
    
    const created = await sendEvents(batch, batchNum);
    totalCreated += created;
    batchNum++;
    
    // Small delay between batches
    await new Promise(r => setTimeout(r, 300));
  }

  console.log('\n' + '='.repeat(70));
  
  // Calculate totals by provider
  const providerTotals = {};
  const modelCounts = {};
  testData.forEach(d => {
    const cost = (d.inputCost || 0) + (d.outputCost || 0);
    providerTotals[d.provider] = (providerTotals[d.provider] || 0) + cost;
    modelCounts[d.model] = (modelCounts[d.model] || 0) + 1;
  });
  
  console.log(`\n📊 Summary:`);
  console.log(`   Total events sent: ${testData.length}`);
  console.log(`   Successfully created: ${totalCreated}`);
  
  console.log(`\n📈 Expected costs by provider:`);
  Object.entries(providerTotals).sort((a, b) => b[1] - a[1]).forEach(([provider, cost]) => {
    console.log(`   ${provider}: $${cost.toFixed(6)}`);
  });
  
  console.log(`\n🔢 Events by model:`);
  Object.entries(modelCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).forEach(([model, count]) => {
    console.log(`   ${model}: ${count}`);
  });
  
  console.log('\n✅ Data generation complete!');
  console.log('🔗 Check dashboard: https://app.llmobserve.com/dashboard\n');
}

main().catch(console.error);

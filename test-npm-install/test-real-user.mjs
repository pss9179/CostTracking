// Test llmobserve with REAL user API key
import { observe, flush } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve with PRODUCTION collector and real user key
observe({
  collectorUrl: 'https://api.llmobserve.com',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789',
  debug: true
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

console.log('\n🔄 Making OpenAI API call (tracking to REAL user account)...\n');

try {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'What is 2 + 2? Answer with just the number.' }],
    max_tokens: 10
  });

  console.log('Response:', response.choices[0].message.content);
  console.log('\nUsage:', response.usage);
  console.log('\n✅ OpenAI call completed!');
} catch (e) {
  console.error('❌ OpenAI call failed:', e.message);
}

// Flush to send all events to the real collector
console.log('\n📤 Flushing events to https://api.llmobserve.com ...');
try {
  await flush();
  console.log('✅ Events sent to collector successfully!');
  console.log('\n🎉 Check the dashboard for this user to see the cost!');
} catch (e) {
  console.error('❌ Flush failed:', e.message);
}


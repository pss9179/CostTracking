// Test llmobserve with multiple models
import { observe, flush } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve
observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789',
  debug: false  // Less verbose
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

const models = [
  'gpt-4o-mini',
  'gpt-4o',
  'gpt-4-turbo',
  'gpt-3.5-turbo',
  'gpt-4o-mini',
  'gpt-4o',
  'gpt-4o-mini',
  'gpt-3.5-turbo',
  'gpt-4o-mini',
  'gpt-4o',
];

const prompts = [
  'What is 2+2?',
  'Name a color.',
  'Say hello.',
  'What is the capital of Japan?',
  'Name a fruit.',
  'What is 10*10?',
  'Say goodbye.',
  'Name a planet.',
  'What is 5-3?',
  'Name an animal.',
];

console.log('🚀 Running multiple model tests...\n');

let totalCost = 0;
let successCount = 0;

for (let i = 0; i < models.length; i++) {
  const model = models[i];
  const prompt = prompts[i];
  
  try {
    const response = await openai.chat.completions.create({
      model: model,
      messages: [{ role: 'user', content: prompt + ' Answer in 1-3 words only.' }],
      max_tokens: 20
    });

    const answer = response.choices[0].message.content;
    const tokens = response.usage.total_tokens;
    
    console.log(`✅ ${model}: "${prompt}" → "${answer}" (${tokens} tokens)`);
    successCount++;
  } catch (e) {
    console.error(`❌ ${model}: ${e.message}`);
  }
  
  // Small delay to avoid rate limiting
  await new Promise(r => setTimeout(r, 500));
}

console.log(`\n📊 Completed ${successCount}/${models.length} calls`);
console.log('📤 Flushing events...');

await flush();

console.log('✅ All events sent to collector!');
console.log('🎉 Check the dashboard to see all the costs!');


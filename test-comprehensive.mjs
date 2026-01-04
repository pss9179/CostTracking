// Comprehensive test script for LLMObserve dashboard
// This will test multiple models across OpenAI to fill up the dashboard

import { observe, flush, section } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve with the real user API key
observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789'
});

const openai = new OpenAI();

// Models to test
const models = [
  // GPT-4 family
  'gpt-4',
  'gpt-4-turbo',
  'gpt-4-turbo-preview',
  'gpt-4o',
  'gpt-4o-mini',
  // GPT-3.5 family
  'gpt-3.5-turbo',
  'gpt-3.5-turbo-0125',
  'gpt-3.5-turbo-1106',
];

// Different prompts to vary the token usage
const prompts = [
  "Say 'hello' in one word.",
  "What is 2+2? Answer briefly.",
  "Name one color.",
  "What day comes after Monday? One word.",
  "Is the sky blue? Yes or no.",
  "Count to 3.",
  "What is the capital of France? One word.",
  "Name a fruit.",
  "What season comes after winter?",
  "Is water wet? Yes or no.",
];

async function makeCall(model, prompt, index) {
  try {
    console.log(`[${index}] Calling ${model}...`);
    const start = Date.now();
    
    const response = await openai.chat.completions.create({
      model: model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 10,
    });
    
    const duration = Date.now() - start;
    console.log(`[${index}] ✅ ${model}: "${response.choices[0].message.content}" (${duration}ms)`);
    return true;
  } catch (error) {
    console.log(`[${index}] ❌ ${model}: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starting comprehensive LLMObserve test...\n');
  console.log('='.repeat(60));
  
  let successCount = 0;
  let failCount = 0;
  let callIndex = 0;

  // Make multiple calls per model to build up data
  for (const model of models) {
    console.log(`\n📦 Testing model: ${model}`);
    console.log('-'.repeat(40));
    
    // Make 3-5 calls per model
    const callsPerModel = Math.floor(Math.random() * 3) + 3; // 3-5 calls
    
    for (let i = 0; i < callsPerModel; i++) {
      callIndex++;
      const prompt = prompts[Math.floor(Math.random() * prompts.length)];
      const success = await makeCall(model, prompt, callIndex);
      
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
      
      // Small delay between calls
      await new Promise(r => setTimeout(r, 200));
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log(`\n📊 Test Summary:`);
  console.log(`   Total calls: ${callIndex}`);
  console.log(`   Successful: ${successCount}`);
  console.log(`   Failed: ${failCount}`);
  
  console.log('\n⏳ Flushing events to collector...');
  await flush();
  
  console.log('✅ All events flushed!');
  console.log('\n🎉 Test complete! Check the dashboard at https://app.llmobserve.com/dashboard');
}

runTests().catch(console.error);

// This will test multiple models across OpenAI to fill up the dashboard

import { observe, flush, section } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve with the real user API key
observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789'
});

const openai = new OpenAI();

// Models to test
const models = [
  // GPT-4 family
  'gpt-4',
  'gpt-4-turbo',
  'gpt-4-turbo-preview',
  'gpt-4o',
  'gpt-4o-mini',
  // GPT-3.5 family
  'gpt-3.5-turbo',
  'gpt-3.5-turbo-0125',
  'gpt-3.5-turbo-1106',
];

// Different prompts to vary the token usage
const prompts = [
  "Say 'hello' in one word.",
  "What is 2+2? Answer briefly.",
  "Name one color.",
  "What day comes after Monday? One word.",
  "Is the sky blue? Yes or no.",
  "Count to 3.",
  "What is the capital of France? One word.",
  "Name a fruit.",
  "What season comes after winter?",
  "Is water wet? Yes or no.",
];

async function makeCall(model, prompt, index) {
  try {
    console.log(`[${index}] Calling ${model}...`);
    const start = Date.now();
    
    const response = await openai.chat.completions.create({
      model: model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 10,
    });
    
    const duration = Date.now() - start;
    console.log(`[${index}] ✅ ${model}: "${response.choices[0].message.content}" (${duration}ms)`);
    return true;
  } catch (error) {
    console.log(`[${index}] ❌ ${model}: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starting comprehensive LLMObserve test...\n');
  console.log('='.repeat(60));
  
  let successCount = 0;
  let failCount = 0;
  let callIndex = 0;

  // Make multiple calls per model to build up data
  for (const model of models) {
    console.log(`\n📦 Testing model: ${model}`);
    console.log('-'.repeat(40));
    
    // Make 3-5 calls per model
    const callsPerModel = Math.floor(Math.random() * 3) + 3; // 3-5 calls
    
    for (let i = 0; i < callsPerModel; i++) {
      callIndex++;
      const prompt = prompts[Math.floor(Math.random() * prompts.length)];
      const success = await makeCall(model, prompt, callIndex);
      
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
      
      // Small delay between calls
      await new Promise(r => setTimeout(r, 200));
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log(`\n📊 Test Summary:`);
  console.log(`   Total calls: ${callIndex}`);
  console.log(`   Successful: ${successCount}`);
  console.log(`   Failed: ${failCount}`);
  
  console.log('\n⏳ Flushing events to collector...');
  await flush();
  
  console.log('✅ All events flushed!');
  console.log('\n🎉 Test complete! Check the dashboard at https://app.llmobserve.com/dashboard');
}

runTests().catch(console.error);

// This will test multiple models across OpenAI to fill up the dashboard

import { observe, flush, section } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve with the real user API key
observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789'
});

const openai = new OpenAI();

// Models to test
const models = [
  // GPT-4 family
  'gpt-4',
  'gpt-4-turbo',
  'gpt-4-turbo-preview',
  'gpt-4o',
  'gpt-4o-mini',
  // GPT-3.5 family
  'gpt-3.5-turbo',
  'gpt-3.5-turbo-0125',
  'gpt-3.5-turbo-1106',
];

// Different prompts to vary the token usage
const prompts = [
  "Say 'hello' in one word.",
  "What is 2+2? Answer briefly.",
  "Name one color.",
  "What day comes after Monday? One word.",
  "Is the sky blue? Yes or no.",
  "Count to 3.",
  "What is the capital of France? One word.",
  "Name a fruit.",
  "What season comes after winter?",
  "Is water wet? Yes or no.",
];

async function makeCall(model, prompt, index) {
  try {
    console.log(`[${index}] Calling ${model}...`);
    const start = Date.now();
    
    const response = await openai.chat.completions.create({
      model: model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 10,
    });
    
    const duration = Date.now() - start;
    console.log(`[${index}] ✅ ${model}: "${response.choices[0].message.content}" (${duration}ms)`);
    return true;
  } catch (error) {
    console.log(`[${index}] ❌ ${model}: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starting comprehensive LLMObserve test...\n');
  console.log('='.repeat(60));
  
  let successCount = 0;
  let failCount = 0;
  let callIndex = 0;

  // Make multiple calls per model to build up data
  for (const model of models) {
    console.log(`\n📦 Testing model: ${model}`);
    console.log('-'.repeat(40));
    
    // Make 3-5 calls per model
    const callsPerModel = Math.floor(Math.random() * 3) + 3; // 3-5 calls
    
    for (let i = 0; i < callsPerModel; i++) {
      callIndex++;
      const prompt = prompts[Math.floor(Math.random() * prompts.length)];
      const success = await makeCall(model, prompt, callIndex);
      
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
      
      // Small delay between calls
      await new Promise(r => setTimeout(r, 200));
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log(`\n📊 Test Summary:`);
  console.log(`   Total calls: ${callIndex}`);
  console.log(`   Successful: ${successCount}`);
  console.log(`   Failed: ${failCount}`);
  
  console.log('\n⏳ Flushing events to collector...');
  await flush();
  
  console.log('✅ All events flushed!');
  console.log('\n🎉 Test complete! Check the dashboard at https://app.llmobserve.com/dashboard');
}

runTests().catch(console.error);

// This will test multiple models across OpenAI to fill up the dashboard

import { observe, flush, section } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve with the real user API key
observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789'
});

const openai = new OpenAI();

// Models to test
const models = [
  // GPT-4 family
  'gpt-4',
  'gpt-4-turbo',
  'gpt-4-turbo-preview',
  'gpt-4o',
  'gpt-4o-mini',
  // GPT-3.5 family
  'gpt-3.5-turbo',
  'gpt-3.5-turbo-0125',
  'gpt-3.5-turbo-1106',
];

// Different prompts to vary the token usage
const prompts = [
  "Say 'hello' in one word.",
  "What is 2+2? Answer briefly.",
  "Name one color.",
  "What day comes after Monday? One word.",
  "Is the sky blue? Yes or no.",
  "Count to 3.",
  "What is the capital of France? One word.",
  "Name a fruit.",
  "What season comes after winter?",
  "Is water wet? Yes or no.",
];

async function makeCall(model, prompt, index) {
  try {
    console.log(`[${index}] Calling ${model}...`);
    const start = Date.now();
    
    const response = await openai.chat.completions.create({
      model: model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 10,
    });
    
    const duration = Date.now() - start;
    console.log(`[${index}] ✅ ${model}: "${response.choices[0].message.content}" (${duration}ms)`);
    return true;
  } catch (error) {
    console.log(`[${index}] ❌ ${model}: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starting comprehensive LLMObserve test...\n');
  console.log('='.repeat(60));
  
  let successCount = 0;
  let failCount = 0;
  let callIndex = 0;

  // Make multiple calls per model to build up data
  for (const model of models) {
    console.log(`\n📦 Testing model: ${model}`);
    console.log('-'.repeat(40));
    
    // Make 3-5 calls per model
    const callsPerModel = Math.floor(Math.random() * 3) + 3; // 3-5 calls
    
    for (let i = 0; i < callsPerModel; i++) {
      callIndex++;
      const prompt = prompts[Math.floor(Math.random() * prompts.length)];
      const success = await makeCall(model, prompt, callIndex);
      
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
      
      // Small delay between calls
      await new Promise(r => setTimeout(r, 200));
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log(`\n📊 Test Summary:`);
  console.log(`   Total calls: ${callIndex}`);
  console.log(`   Successful: ${successCount}`);
  console.log(`   Failed: ${failCount}`);
  
  console.log('\n⏳ Flushing events to collector...');
  await flush();
  
  console.log('✅ All events flushed!');
  console.log('\n🎉 Test complete! Check the dashboard at https://app.llmobserve.com/dashboard');
}

runTests().catch(console.error);

// This will test multiple models across OpenAI to fill up the dashboard

import { observe, flush, section } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve with the real user API key
observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789'
});

const openai = new OpenAI();

// Models to test
const models = [
  // GPT-4 family
  'gpt-4',
  'gpt-4-turbo',
  'gpt-4-turbo-preview',
  'gpt-4o',
  'gpt-4o-mini',
  // GPT-3.5 family
  'gpt-3.5-turbo',
  'gpt-3.5-turbo-0125',
  'gpt-3.5-turbo-1106',
];

// Different prompts to vary the token usage
const prompts = [
  "Say 'hello' in one word.",
  "What is 2+2? Answer briefly.",
  "Name one color.",
  "What day comes after Monday? One word.",
  "Is the sky blue? Yes or no.",
  "Count to 3.",
  "What is the capital of France? One word.",
  "Name a fruit.",
  "What season comes after winter?",
  "Is water wet? Yes or no.",
];

async function makeCall(model, prompt, index) {
  try {
    console.log(`[${index}] Calling ${model}...`);
    const start = Date.now();
    
    const response = await openai.chat.completions.create({
      model: model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 10,
    });
    
    const duration = Date.now() - start;
    console.log(`[${index}] ✅ ${model}: "${response.choices[0].message.content}" (${duration}ms)`);
    return true;
  } catch (error) {
    console.log(`[${index}] ❌ ${model}: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starting comprehensive LLMObserve test...\n');
  console.log('='.repeat(60));
  
  let successCount = 0;
  let failCount = 0;
  let callIndex = 0;

  // Make multiple calls per model to build up data
  for (const model of models) {
    console.log(`\n📦 Testing model: ${model}`);
    console.log('-'.repeat(40));
    
    // Make 3-5 calls per model
    const callsPerModel = Math.floor(Math.random() * 3) + 3; // 3-5 calls
    
    for (let i = 0; i < callsPerModel; i++) {
      callIndex++;
      const prompt = prompts[Math.floor(Math.random() * prompts.length)];
      const success = await makeCall(model, prompt, callIndex);
      
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
      
      // Small delay between calls
      await new Promise(r => setTimeout(r, 200));
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log(`\n📊 Test Summary:`);
  console.log(`   Total calls: ${callIndex}`);
  console.log(`   Successful: ${successCount}`);
  console.log(`   Failed: ${failCount}`);
  
  console.log('\n⏳ Flushing events to collector...');
  await flush();
  
  console.log('✅ All events flushed!');
  console.log('\n🎉 Test complete! Check the dashboard at https://app.llmobserve.com/dashboard');
}

runTests().catch(console.error);




















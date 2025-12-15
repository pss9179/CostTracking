// More comprehensive test with many calls
import { observe, flush, section } from 'llmobserve';
import OpenAI from 'openai';

observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789',
  debug: false
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

console.log('🚀 Running comprehensive model tests...\n');

// Batch 1: Quick math questions
console.log('📐 Math Questions (gpt-4o-mini)...');
for (let i = 1; i <= 5; i++) {
  const a = Math.floor(Math.random() * 100);
  const b = Math.floor(Math.random() * 100);
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: `What is ${a} + ${b}? Just the number.` }],
    max_tokens: 10
  });
  console.log(`  ${a} + ${b} = ${response.choices[0].message.content}`);
  await new Promise(r => setTimeout(r, 300));
}

// Batch 2: Creative with GPT-4o
console.log('\n🎨 Creative (gpt-4o)...');
const creativePrompts = [
  'Invent a word and define it.',
  'Name a fictional planet.',
  'Create a superhero name.',
  'Invent a new food dish name.',
  'Name a mythical creature.',
];
for (const prompt of creativePrompts) {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: prompt + ' Keep it under 10 words.' }],
    max_tokens: 30
  });
  console.log(`  ${prompt.slice(0, 25)}... → ${response.choices[0].message.content}`);
  await new Promise(r => setTimeout(r, 300));
}

// Batch 3: Fast responses with GPT-3.5
console.log('\n⚡ Fast Q&A (gpt-3.5-turbo)...');
const quickQuestions = [
  'Capital of France?',
  'Largest ocean?',
  'Fastest land animal?',
  'Chemical symbol for gold?',
  'Year WW2 ended?',
  'Smallest planet?',
  'Author of Hamlet?',
  'Tallest mountain?',
];
for (const q of quickQuestions) {
  const response = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: q + ' One word answer.' }],
    max_tokens: 10
  });
  console.log(`  ${q} → ${response.choices[0].message.content}`);
  await new Promise(r => setTimeout(r, 200));
}

// Batch 4: Using sections for grouping
console.log('\n📦 Sectioned calls (customer-support simulation)...');
await section('customer-support').run(async () => {
  const tickets = [
    'How do I reset my password?',
    'What are your business hours?',
    'Can I get a refund?',
  ];
  for (const ticket of tickets) {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a helpful customer support agent. Be brief.' },
        { role: 'user', content: ticket }
      ],
      max_tokens: 50
    });
    console.log(`  Q: ${ticket}`);
    console.log(`  A: ${response.choices[0].message.content.slice(0, 60)}...`);
    await new Promise(r => setTimeout(r, 300));
  }
});

// Batch 5: Code generation with GPT-4
console.log('\n💻 Code snippets (gpt-4-turbo)...');
const codePrompts = [
  'Write a one-line Python hello world',
  'Write a one-line JavaScript arrow function',
  'Write a SQL SELECT statement',
];
for (const prompt of codePrompts) {
  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo',
    messages: [{ role: 'user', content: prompt + '. Just the code, no explanation.' }],
    max_tokens: 40
  });
  console.log(`  ${prompt.slice(0, 30)}... → ${response.choices[0].message.content.slice(0, 50)}`);
  await new Promise(r => setTimeout(r, 300));
}

// Batch 6: More GPT-4o-mini for volume
console.log('\n📊 Volume test (gpt-4o-mini x10)...');
for (let i = 1; i <= 10; i++) {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: `Count to ${i}. Just numbers.` }],
    max_tokens: 20
  });
  process.stdout.write(`  Call ${i}: ${response.choices[0].message.content.slice(0, 20)}... ✓\n`);
  await new Promise(r => setTimeout(r, 200));
}

console.log('\n📤 Flushing all events...');
await flush();

console.log('\n✅ Done! Total calls made: ~36');
console.log('🎉 Check the dashboard for all costs broken down by model!');


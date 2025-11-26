const { observe } = require('llmobserve');
const OpenAI = require('openai');

// Initialize observability
observe({
    collectorUrl: "http://localhost:8000",
    apiKey: "llmo_sk_4b43bb4e94e87a907ffbb4b06d1f1364d126bbe67135d538",
    flushIntervalMs: 100 // Fast flush for testing
});

const client = new OpenAI({
    apiKey: "sk-proj-1234567890", // Fake key, we'll mock the response or expect error but tracking should happen
});

async function main() {
    console.log("Starting test...");

    // Mock fetch to avoid actual OpenAI call but test interception
    const originalFetch = global.fetch;
    global.fetch = async (input, init) => {
        const url = input.toString();
        if (url.includes("api.openai.com")) {
            console.log("Mocking OpenAI response...");
            return new Response(JSON.stringify({
                id: "chatcmpl-123",
                object: "chat.completion",
                created: Date.now(),
                model: "gpt-4o-mini",
                choices: [{
                    index: 0,
                    message: { role: "assistant", content: "Hello from mock!" },
                    finish_reason: "stop"
                }],
                usage: {
                    prompt_tokens: 10,
                    completion_tokens: 5,
                    total_tokens: 15
                }
            }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
        return originalFetch(input, init);
    };

    try {
        const completion = await client.chat.completions.create({
            messages: [{ role: "user", content: "Hello world" }],
            model: "gpt-4o-mini",
        });

        console.log("Response:", completion.choices[0].message.content);

        // Wait for flush
        console.log("Waiting for flush...");
        await new Promise(resolve => setTimeout(resolve, 2000));
        console.log("Done!");
    } catch (error) {
        console.error("Error:", error);
    }
}

main();

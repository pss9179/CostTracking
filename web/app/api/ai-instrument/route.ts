import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

/**
 * AI-powered code instrumentation endpoint.
 * Uses Claude API (backend key) to analyze Python code and suggest LLMObserve labels.
 */
export async function POST(request: NextRequest) {
  try {
    // Authenticate user
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json(
        { error: "Unauthorized - please sign in" },
        { status: 401 }
      );
    }

    // Parse request body
    const body = await request.json();
    const { code, file_path } = body;

    if (!code) {
      return NextResponse.json(
        { error: "Missing 'code' in request body" },
        { status: 400 }
      );
    }

    // Check for Anthropic API key
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    if (!anthropicKey) {
      console.error("[ai-instrument] ANTHROPIC_API_KEY not set");
      return NextResponse.json(
        { error: "AI instrumentation not configured" },
        { status: 500 }
      );
    }

    // Call Anthropic API
    const anthropicResponse = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": anthropicKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 4000,
        temperature: 0,
        messages: [
          {
            role: "user",
            content: buildAnalysisPrompt(code, file_path),
          },
        ],
      }),
    });

    if (!anthropicResponse.ok) {
      const errorText = await anthropicResponse.text();
      console.error("[ai-instrument] Anthropic API error:", errorText);
      return NextResponse.json(
        { error: "Failed to analyze code" },
        { status: 500 }
      );
    }

    const anthropicData = await anthropicResponse.json();
    const responseText = anthropicData.content[0].text;

    // Parse suggestions from response
    const suggestions = parseResponse(responseText);

    return NextResponse.json({
      file_path,
      suggestions,
      response_text: responseText,
    });
  } catch (error) {
    console.error("[ai-instrument] Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}

function buildAnalysisPrompt(code: string, filePath?: string): string {
  return `You are an expert Python developer helping instrument code for LLMObserve cost tracking.

LLMObserve tracks LLM API costs using these labeling methods:

1. **@agent decorator** - Mark agent entry points:
\`\`\`python
from llmobserve import agent

@agent("researcher")
def research_agent(query):
    # All API calls here auto-labeled as "agent:researcher"
    return result
\`\`\`

2. **section() context manager** - Label code blocks:
\`\`\`python
from llmobserve import section

with section("agent:researcher"):
    # All API calls here auto-labeled
    response = openai_call()
\`\`\`

3. **wrap_all_tools()** - Wrap tool lists for frameworks:
\`\`\`python
from llmobserve import wrap_all_tools

tools = [web_search, calculator]
wrapped_tools = wrap_all_tools(tools)
agent = Agent(tools=wrapped_tools)  # LangChain, CrewAI, etc.
\`\`\`

**Your task:**
Analyze this Python code and suggest where to add LLMObserve instrumentation.

**Focus on:**
- Functions that orchestrate LLM calls (likely agents)
- Framework usage (LangChain, CrewAI, AutoGen, LlamaIndex)
- Tool definitions
- Multi-step workflows

**Output format:**
Return ONLY valid JSON with this structure:
\`\`\`json
{
  "suggestions": [
    {
      "type": "decorator" | "context_manager" | "wrap_tools",
      "line_number": <int>,
      "function_name": "<name>",
      "suggested_label": "<label>",
      "code_before": "<original line>",
      "code_after": "<modified line>",
      "reason": "<why this needs instrumentation>"
    }
  ]
}
\`\`\`

**File:** ${filePath || "N/A"}

**Code to analyze:**
\`\`\`python
${code}
\`\`\`

**Important:**
- Return ONLY JSON, no markdown or explanations
- Suggest agent names based on function purpose (e.g., "researcher", "writer", "analyzer")
- For LangChain agents, suggest wrap_all_tools() on the tools list
- Don't suggest instrumentation for non-LLM code
- Be conservative - only suggest where it clearly makes sense`;
}

function parseResponse(responseText: string): any[] {
  try {
    // Try to extract JSON from response
    // Sometimes Claude wraps it in markdown
    const jsonMatch = responseText.match(/```json\s*\n(.*?)\n```/s);
    const jsonText = jsonMatch ? jsonMatch[1] : responseText.trim();
    
    const data = JSON.parse(jsonText);
    return data.suggestions || [];
  } catch (error) {
    console.error("[ai-instrument] Failed to parse response:", error);
    console.debug("[ai-instrument] Response text:", responseText);
    return [];
  }
}


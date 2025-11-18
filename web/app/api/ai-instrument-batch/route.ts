import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

/**
 * Batch AI instrumentation endpoint.
 * Processes multiple files at once for better efficiency.
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
    const { files, custom_instructions } = body;

    if (!files || !Array.isArray(files)) {
      return NextResponse.json(
        { error: "Missing 'files' array in request body" },
        { status: 400 }
      );
    }

    // Check for Anthropic API key
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    if (!anthropicKey) {
      console.error("[ai-instrument-batch] ANTHROPIC_API_KEY not set");
      return NextResponse.json(
        { error: "AI instrumentation not configured" },
        { status: 500 }
      );
    }

    // Build batch prompt
    const prompt = buildBatchPrompt(files, custom_instructions);

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
        max_tokens: 8000,
        temperature: 0,
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
      }),
    });

    if (!anthropicResponse.ok) {
      const errorText = await anthropicResponse.text();
      console.error("[ai-instrument-batch] Anthropic API error:", errorText);
      return NextResponse.json(
        { error: "Failed to analyze code" },
        { status: 500 }
      );
    }

    const anthropicData = await anthropicResponse.json();
    const responseText = anthropicData.content[0].text;

    // Parse results
    const results = parseResponse(responseText, files);

    return NextResponse.json({ results });
  } catch (error) {
    console.error("[ai-instrument-batch] Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}

function buildBatchPrompt(files: any[], customInstructions?: string): string {
  const customNote = customInstructions 
    ? `\n\n**User Instructions:**\n${customInstructions}\n` 
    : "";

  const filesDesc = files.map((f, i) => `
**File ${i + 1}: ${f.file_path}**
Language: ${f.language}
Confidence: ${(f.confidence * 100).toFixed(0)}%
Reasons: ${f.reasons.join(", ")}
LLM calls detected: ${f.llm_calls?.length || 0}
Agent patterns: ${f.agent_patterns?.length || 0}
  `).join("\n");

  return `You are analyzing a codebase to suggest LLMObserve instrumentation.

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
agent = Agent(tools=wrapped_tools)
\`\`\`

${customNote}

Analyze these files and suggest minimal, safe patches:

${filesDesc}

For each file, return:
1. file_path
2. suggestions array with:
   - label: meaningful agent/tool name
   - patch_type: "decorator", "context_manager", or "wrap_tools"
   - line_number: exact line
   - function_name: if applicable
   - code_before: original line
   - code_after: modified line
   - reason: why this needs instrumentation
   - confidence: 0.0-1.0
3. unified_patch: unified diff format
4. needs_review: true if uncertain
5. reasoning: brief explanation

Return ONLY valid JSON with this structure:
\`\`\`json
{
  "results": [
    {
      "file_path": "...",
      "suggestions": [...],
      "unified_patch": "...",
      "needs_review": false,
      "reasoning": "..."
    }
  ]
}
\`\`\`

Be conservative. Only suggest changes where you're highly confident.`;
}

function parseResponse(responseText: string, files: any[]): any[] {
  try {
    // Try to extract JSON from response
    const jsonMatch = responseText.match(/```json\s*\n([\s\S]*?)\n```/);
    const jsonText = jsonMatch ? jsonMatch[1] : responseText.trim();
    
    const data = JSON.parse(jsonText);
    return data.results || [];
  } catch (error) {
    console.error("[ai-instrument-batch] Failed to parse response:", error);
    console.debug("[ai-instrument-batch] Response text:", responseText);
    
    // Return empty results for each file
    return files.map(f => ({
      file_path: f.file_path,
      suggestions: [],
      unified_patch: "",
      needs_review: false,
      reasoning: "Failed to parse AI response"
    }));
  }
}


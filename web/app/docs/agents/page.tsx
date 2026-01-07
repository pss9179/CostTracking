"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "why-label-agents", title: "Why label agents?" },
  { id: "agent-decorator", title: "@agent decorator" },
  { id: "section-context", title: "section() context manager" },
  { id: "wrap-tools", title: "wrap_all_tools()" },
  { id: "framework-examples", title: "Framework examples" },
  { id: "viewing-agent-costs", title: "Viewing agent costs" },
];

export default function AgentsPage() {
  return (
    <DocPage
      title="Agent tracking"
      description="Label costs by agent, tool, or workflow to understand exactly where your LLM spending goes."
      category="Labeling & organization"
      toc={toc}
    >
      <h2 id="why-label-agents">Why label agents?</h2>

      <p>
        LLMObserve automatically tracks <strong>all</strong> your LLM API calls. However, without 
        labels, all costs appear as "Untracked" in your dashboard. By adding labels, you can:
      </p>

      <ul>
        <li>See costs broken down by agent (researcher, writer, analyst)</li>
        <li>Track costs for individual tools (web_search, calculator)</li>
        <li>Identify which workflows are most expensive</li>
        <li>Optimize specific parts of your application</li>
      </ul>

      <Callout type="tip">
        You don't <em>have</em> to label agents. LLMObserve still tracks everything. 
        Labels just help you organize and analyze your costs.
      </Callout>

      <h2 id="agent-decorator">@agent decorator</h2>

      <p>
        The simplest way to label an agent. All LLM calls within the decorated function 
        are automatically labeled.
      </p>

      <CodeBlock
        code={`from llmobserve import observe, agent
from openai import OpenAI

observe(api_key="...")
client = OpenAI()

@agent("researcher")
def research_workflow(query: str):
    # All LLM calls here are labeled "agent:researcher"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Research: {query}"}]
    )
    return response.choices[0].message.content

@agent("writer")
def writing_workflow(topic: str):
    # All LLM calls here are labeled "agent:writer"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Write about: {topic}"}]
    )
    return response.choices[0].message.content

# Use your agents
research = research_workflow("quantum computing")
article = writing_workflow(research)`}
        language="python"
        filename="main.py"
      />

      <h3>Nested agents</h3>

      <p>Agent decorators can be nested. Inner calls inherit the outer agent's label.</p>

      <CodeBlock
        code={`@agent("orchestrator")
def main_workflow():
    # Labeled "agent:orchestrator"
    research_result = research_workflow("AI")  # Still "agent:researcher"
    return writing_workflow(research_result)   # Still "agent:writer"`}
        language="python"
      />

      <h2 id="section-context">section() context manager</h2>

      <p>
        For more granular control, use the <code>section()</code> context manager. 
        Perfect for labeling specific code blocks or creating hierarchical labels.
      </p>

      <CodeBlock
        code={`from llmobserve import observe, section
from openai import OpenAI

observe(api_key="...")
client = OpenAI()

# Simple section
with section("agent:researcher"):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Research AI"}]
    )

# Nested sections create hierarchical labels
with section("agent:researcher"):
    with section("tool:web_search"):
        # Labeled "agent:researcher/tool:web_search"
        search_results = search_api.query("AI news")
    
    with section("tool:summarize"):
        # Labeled "agent:researcher/tool:summarize"
        summary = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Summarize: {search_results}"}]
        )`}
        language="python"
        filename="main.py"
      />

      <h2 id="wrap-tools">wrap_all_tools()</h2>

      <p>
        For agent frameworks like LangChain or CrewAI, use <code>wrap_all_tools()</code> to 
        automatically label each tool call.
      </p>

      <CodeBlock
        code={`from llmobserve import observe, wrap_all_tools

observe(api_key="...")

# Your tools
tools = [
    search_tool,      # Will be labeled "tool:search_tool"
    calculator_tool,  # Will be labeled "tool:calculator_tool"
    weather_tool,     # Will be labeled "tool:weather_tool"
]

# Wrap before passing to framework
wrapped_tools = wrap_all_tools(tools)

# Use wrapped tools with your framework
agent = YourAgentFramework(tools=wrapped_tools)`}
        language="python"
        filename="main.py"
      />

      <h2 id="framework-examples">Framework examples</h2>

      <h3>LangChain</h3>

      <CodeBlock
        code={`from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from llmobserve import observe, wrap_all_tools, agent

observe(api_key="...")

# Create tools
tools = [search_tool, calculator_tool]
wrapped_tools = wrap_all_tools(tools)

# Create agent
llm = ChatOpenAI(model="gpt-4o")
agent = create_openai_functions_agent(llm, wrapped_tools, prompt)
executor = AgentExecutor(agent=agent, tools=wrapped_tools)

# Run with agent label
@agent("langchain_agent")
def run_agent(query):
    return executor.invoke({"input": query})`}
        language="python"
        filename="langchain_example.py"
      />

      <h3>CrewAI</h3>

      <CodeBlock
        code={`from crewai import Agent, Task, Crew
from llmobserve import observe, wrap_all_tools, section

observe(api_key="...")

# Wrap tools
tools = wrap_all_tools([search_tool, scraper_tool])

# Create agents
researcher = Agent(
    role="Researcher",
    tools=tools,
    llm="gpt-4o"
)

writer = Agent(
    role="Writer",
    tools=[],
    llm="gpt-4o"
)

# Run crew with section labels
with section("crew:research_team"):
    crew = Crew(agents=[researcher, writer], tasks=[...])
    result = crew.kickoff()`}
        language="python"
        filename="crewai_example.py"
      />

      <h2 id="viewing-agent-costs">Viewing agent costs</h2>

      <p>
        After adding labels, your dashboard shows costs broken down by agent:
      </p>

      <ul>
        <li><strong>Features page</strong> — See all labeled sections with costs, call counts</li>
        <li><strong>Dashboard</strong> — Filter by agent to see just that agent's costs</li>
        <li><strong>Individual runs</strong> — See the agent label for each API call</li>
      </ul>

      <Callout type="info" title="What about unlabeled calls?">
        LLM calls made outside of any <code>@agent</code> decorator or <code>section()</code> 
        context appear as "Untracked" in your dashboard. They're still tracked and counted 
        toward your totals.
      </Callout>

      <hr />

      <h3>Next steps</h3>

      <ul>
        <li><Link href="/docs/customers">Customer tracking</Link> — Track costs per customer</li>
        <li><Link href="/docs/sections">Sections & workflows</Link> — Advanced labeling patterns</li>
        <li><Link href="/docs/api/agent">@agent API reference</Link></li>
      </ul>
    </DocPage>
  );
}


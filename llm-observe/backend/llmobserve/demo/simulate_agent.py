"""Simulates an agent workflow using GPT → Pinecone → GPT."""

import asyncio
import openai
from pinecone import Pinecone
from llmobserve.config import settings


async def simulate_agent_workflow() -> dict:
        """Run a simple agent workflow and return results."""
        
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        query_resp = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a search query generator. Generate concise search queries."},
                {"role": "user", "content": "Generate a search query for: What is machine learning?"}
            ],
            max_tokens=50,
            temperature=0.7,
            top_p=1.0,
        )
        query = query_resp.choices[0].message.content
        
        index = Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index_name or "test")
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: index.query(vector=[0.0] * 1024, top_k=3, include_metadata=True)
        )
        
        context = "\n".join([m.get("metadata", {}).get("text", str(m)) for m in results.get("matches", [])[:3]])
        
        summary_resp = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a summarization assistant. Provide concise summaries."},
                {"role": "user", "content": f"Query: {query}\n\nContext:\n{context[:500]}\n\nSummarize the key points."}
            ],
            max_tokens=150,
            temperature=0.5,
            top_p=0.9,
        )
        summary = summary_resp.choices[0].message.content
        
        return {"query": query, "retrieval": results.get("matches", []), "summary": summary}

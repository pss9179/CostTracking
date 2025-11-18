"""
Automatic Framework Patching for Zero-Config Agent Tracking

This module patches popular agent frameworks at import time to automatically
track agents without requiring manual labeling. Works transparently!

Supported Frameworks:
- LangChain (AgentExecutor.run, Agent.run)
- CrewAI (Agent.execute, Crew.kickoff)
- AutoGen (AssistantAgent.generate_reply)
- LlamaIndex (OpenAIAgent.chat, ReActAgent.chat)

Usage:
    Just import llmobserve and frameworks - tracking happens automatically!
    
    from llmobserve import observe
    from langchain.agents import AgentExecutor
    
    observe(collector_url="...", api_key="...")
    
    # Agent tracking happens automatically - no manual labeling needed!
    agent = AgentExecutor(...)
    result = agent.run("query")  # Automatically tracked as agent
"""
import logging
import functools
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

# Track which frameworks have been patched
_patched_frameworks = set()


def auto_patch_frameworks() -> dict:
    """
    Automatically patch popular agent frameworks for zero-config tracking.
    
    This patches agent execution methods directly, which is more reliable
    than constructor patching because it works regardless of how agents
    are created.
    
    Returns:
        Dict mapping framework names to success status
    """
    results = {}
    
    # LangChain
    results["langchain"] = _patch_langchain()
    
    # CrewAI
    results["crewai"] = _patch_crewai()
    
    # AutoGen
    results["autogen"] = _patch_autogen()
    
    # LlamaIndex
    results["llamaindex"] = _patch_llamaindex()
    
    return results


def _patch_langchain() -> bool:
    """Patch LangChain AgentExecutor and Agent classes."""
    try:
        from langchain.agents import AgentExecutor
        from langchain.agents.agent import Agent
        
        # Patch AgentExecutor.run() and .arun()
        if "langchain.AgentExecutor" not in _patched_frameworks:
            if hasattr(AgentExecutor, "run"):
                original_run = AgentExecutor.run
                if not hasattr(original_run, "_llmobserve_patched"):
                    AgentExecutor.run = _wrap_agent_method(original_run, "AgentExecutor")
                    AgentExecutor.run._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched LangChain AgentExecutor.run()")
            
            if hasattr(AgentExecutor, "arun"):
                original_arun = AgentExecutor.arun
                if not hasattr(original_arun, "_llmobserve_patched"):
                    AgentExecutor.arun = _wrap_agent_method_async(original_arun, "AgentExecutor")
                    AgentExecutor.arun._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched LangChain AgentExecutor.arun()")
            
            _patched_frameworks.add("langchain.AgentExecutor")
        
        # Patch Agent.run() and .arun() (for direct agent usage)
        if "langchain.Agent" not in _patched_frameworks:
            if hasattr(Agent, "run"):
                original_run = Agent.run
                if not hasattr(original_run, "_llmobserve_patched"):
                    Agent.run = _wrap_agent_method(original_run, "Agent")
                    Agent.run._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched LangChain Agent.run()")
            
            if hasattr(Agent, "arun"):
                original_arun = Agent.arun
                if not hasattr(original_arun, "_llmobserve_patched"):
                    Agent.arun = _wrap_agent_method_async(original_arun, "Agent")
                    Agent.arun._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched LangChain Agent.arun()")
            
            _patched_frameworks.add("langchain.Agent")
        
        return True
    except ImportError:
        logger.debug("[llmobserve] LangChain not installed, skipping auto-patch")
        return False
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to auto-patch LangChain: {e}")
        return False


def _patch_crewai() -> bool:
    """Patch CrewAI Agent and Crew classes."""
    try:
        from crewai import Agent, Crew
        
        # Patch Agent.execute()
        if "crewai.Agent" not in _patched_frameworks:
            if hasattr(Agent, "execute"):
                original_execute = Agent.execute
                if not hasattr(original_execute, "_llmobserve_patched"):
                    Agent.execute = _wrap_agent_method(original_execute, "Agent")
                    Agent.execute._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched CrewAI Agent.execute()")
            
            _patched_frameworks.add("crewai.Agent")
        
        # Patch Crew.kickoff()
        if "crewai.Crew" not in _patched_frameworks:
            if hasattr(Crew, "kickoff"):
                original_kickoff = Crew.kickoff
                if not hasattr(original_kickoff, "_llmobserve_patched"):
                    Crew.kickoff = _wrap_agent_method(original_kickoff, "Crew")
                    Crew.kickoff._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched CrewAI Crew.kickoff()")
            
            _patched_frameworks.add("crewai.Crew")
        
        return True
    except ImportError:
        logger.debug("[llmobserve] CrewAI not installed, skipping auto-patch")
        return False
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to auto-patch CrewAI: {e}")
        return False


def _patch_autogen() -> bool:
    """Patch AutoGen AssistantAgent."""
    try:
        from autogen import AssistantAgent
        
        # Patch AssistantAgent.generate_reply()
        if "autogen.AssistantAgent" not in _patched_frameworks:
            if hasattr(AssistantAgent, "generate_reply"):
                original_generate_reply = AssistantAgent.generate_reply
                if not hasattr(original_generate_reply, "_llmobserve_patched"):
                    AssistantAgent.generate_reply = _wrap_agent_method(original_generate_reply, "AssistantAgent")
                    AssistantAgent.generate_reply._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched AutoGen AssistantAgent.generate_reply()")
            
            _patched_frameworks.add("autogen.AssistantAgent")
        
        return True
    except ImportError:
        logger.debug("[llmobserve] AutoGen not installed, skipping auto-patch")
        return False
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to auto-patch AutoGen: {e}")
        return False


def _patch_llamaindex() -> bool:
    """Patch LlamaIndex OpenAIAgent and ReActAgent."""
    try:
        # Try OpenAIAgent
        try:
            from llama_index.agent.openai import OpenAIAgent
        except ImportError:
            try:
                from llama_index.agent import OpenAIAgent
            except ImportError:
                OpenAIAgent = None
        
        # Try ReActAgent
        try:
            from llama_index.agent.react import ReActAgent
        except ImportError:
            try:
                from llama_index.agent import ReActAgent
            except ImportError:
                ReActAgent = None
        
        # Patch OpenAIAgent.chat()
        if OpenAIAgent and "llamaindex.OpenAIAgent" not in _patched_frameworks:
            if hasattr(OpenAIAgent, "chat"):
                original_chat = OpenAIAgent.chat
                if not hasattr(original_chat, "_llmobserve_patched"):
                    OpenAIAgent.chat = _wrap_agent_method(original_chat, "OpenAIAgent")
                    OpenAIAgent.chat._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched LlamaIndex OpenAIAgent.chat()")
            
            _patched_frameworks.add("llamaindex.OpenAIAgent")
        
        # Patch ReActAgent.chat()
        if ReActAgent and "llamaindex.ReActAgent" not in _patched_frameworks:
            if hasattr(ReActAgent, "chat"):
                original_chat = ReActAgent.chat
                if not hasattr(original_chat, "_llmobserve_patched"):
                    ReActAgent.chat = _wrap_agent_method(original_chat, "ReActAgent")
                    ReActAgent.chat._llmobserve_patched = True
                    logger.info("[llmobserve] ✓ Auto-patched LlamaIndex ReActAgent.chat()")
            
            _patched_frameworks.add("llamaindex.ReActAgent")
        
        return True
    except ImportError:
        logger.debug("[llmobserve] LlamaIndex not installed, skipping auto-patch")
        return False
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to auto-patch LlamaIndex: {e}")
        return False


def _wrap_agent_method(original_method: Callable, agent_class_name: str) -> Callable:
    """Wrap a sync agent method to automatically create agent context."""
    from llmobserve.context import section
    
    @functools.wraps(original_method)
    def wrapped_method(self, *args, **kwargs):
        # Extract agent name from agent object
        agent_name = _extract_agent_name(self, agent_class_name)
        
        # Create agent section context
        with section(f"agent:{agent_name}"):
            return original_method(self, *args, **kwargs)
    
    return wrapped_method


def _wrap_agent_method_async(original_method: Callable, agent_class_name: str) -> Callable:
    """Wrap an async agent method to automatically create agent context."""
    from llmobserve.context import section
    
    @functools.wraps(original_method)
    async def wrapped_method(self, *args, **kwargs):
        # Extract agent name from agent object
        agent_name = _extract_agent_name(self, agent_class_name)
        
        # Create agent section context
        with section(f"agent:{agent_name}"):
            return await original_method(self, *args, **kwargs)
    
    return wrapped_method


def _extract_agent_name(agent_obj: Any, default_name: str) -> str:
    """Extract a meaningful agent name from agent object."""
    # Try various attributes that frameworks use for agent names
    name_attrs = ["name", "role", "agent_name", "agent_role", "role_name", "id"]
    
    for attr in name_attrs:
        if hasattr(agent_obj, attr):
            value = getattr(agent_obj, attr)
            if value and isinstance(value, str):
                # Clean up the name
                name = value.lower().replace(" ", "_").replace("-", "_")
                if name:
                    return name
    
    # Fall back to class name or default
    class_name = agent_obj.__class__.__name__ if hasattr(agent_obj, "__class__") else default_name
    return class_name.lower().replace(" ", "_")


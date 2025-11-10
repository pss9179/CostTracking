#!/usr/bin/env python3
"""
Test runner for complex nested workflows.

Usage:
    python run_complex_workflows.py [workflow_number]
    
    workflow_number: 1-5 to run a specific workflow, or omit to run all
"""

import asyncio
import sys
from llmobserve.demo.complex_nested_workflows import (
    gpt_vapi_google_workflow,
    vapi_google_pinecone_workflow,
    nested_async_workflow,
    parallel_workflows_with_nesting,
    deeply_nested_workflow,
    run_all_complex_workflows,
)


async def run_workflow(workflow_num: int):
    """Run a specific workflow by number."""
    workflows = {
        1: ("GPT + Vapi + Google Calendar", gpt_vapi_google_workflow),
        2: ("Vapi + Google Calendar + Pinecone", vapi_google_pinecone_workflow),
        3: ("Nested Async Workflow (MOST COMPLEX)", nested_async_workflow),
        4: ("Parallel Workflows", parallel_workflows_with_nesting),
        5: ("Deeply Nested Workflow", deeply_nested_workflow),
    }
    
    if workflow_num not in workflows:
        print(f"Invalid workflow number: {workflow_num}")
        print("Valid options: 1-5")
        return
    
    name, func = workflows[workflow_num]
    print(f"\n{'='*80}")
    print(f"Running Workflow {workflow_num}: {name}")
    print(f"{'='*80}\n")
    
    try:
        result = await func()
        print(f"\n✅ Workflow {workflow_num} completed successfully!")
        print(f"Result keys: {list(result.keys())}")
        print(f"\nCheck your tracing UI to see the workflow trace!")
        return result
    except Exception as e:
        print(f"\n❌ Workflow {workflow_num} failed with error:")
        print(f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        try:
            workflow_num = int(sys.argv[1])
            await run_workflow(workflow_num)
        except ValueError:
            print(f"Invalid workflow number: {sys.argv[1]}")
            print("Usage: python run_complex_workflows.py [1-5]")
            sys.exit(1)
    else:
        print("\n" + "="*80)
        print("Running ALL Complex Workflows")
        print("="*80 + "\n")
        
        results = await run_all_complex_workflows()
        
        print("\n" + "="*80)
        print("ALL WORKFLOWS COMPLETED")
        print("="*80)
        print(f"Total workflows executed: {results['total_workflows']}")
        print("\nWorkflow Descriptions:")
        for key, desc in results['workflow_descriptions'].items():
            print(f"  - {key}: {desc}")
        print("\n✅ Check your tracing UI to see all workflow traces!")
        print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())


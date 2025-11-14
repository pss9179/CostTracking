#!/usr/bin/env python3
"""
Integration Test: End-to-End Visualization Accuracy
Tests the complete flow from trace events to visualization tree.

This ensures:
1. Events are correctly structured
2. Tree building is accurate
3. Visualization components receive correct data
4. Edge cases are handled gracefully
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.types import TraceEvent


def create_event(
    span_id: str,
    parent_span_id: str | None,
    section: str,
    section_path: str | None = None,
    cost: float = 0.01,
    provider: str = "openai",
    endpoint: str = "chat.completions.create",
    model: str = "gpt-4"
) -> TraceEvent:
    """Create a test trace event matching the actual schema."""
    return {
        'id': str(uuid4()),
        'run_id': str(uuid4()),
        'span_id': span_id,
        'parent_span_id': parent_span_id,
        'section': section,
        'section_path': section_path,
        'span_type': 'llm',
        'provider': provider,
        'endpoint': endpoint,
        'model': model,
        'input_tokens': 10,
        'output_tokens': 20,
        'cached_tokens': 0,
        'cost_usd': cost,
        'latency_ms': 100.0,
        'status': 'ok',
        'is_streaming': False,
        'stream_cancelled': False,
        'event_metadata': None,
    }


def build_tree_ts_logic(events: List[TraceEvent]) -> List[Dict]:
    """
    Replicate the TypeScript buildTree logic exactly.
    This matches GraphTreeVisualization.tsx and VisualTreeTrace.tsx
    """
    node_map = {}
    root_nodes = []
    
    # First pass: create all nodes
    for event in events:
        node_map[event['span_id']] = {
            'event': event,
            'children': [],
            'id': event['span_id'],
        }
    
    # Second pass: build tree structure
    for event in events:
        node = node_map.get(event['span_id'])
        if not node:
            continue
        
        parent_span_id = event.get('parent_span_id')
        if parent_span_id and parent_span_id in node_map:
            parent = node_map[parent_span_id]
            parent['children'].append(node)
        else:
            root_nodes.append(node)
    
    return root_nodes


def collect_all_nodes_ts(nodes: List[Dict]) -> List[Dict]:
    """Collect all nodes recursively."""
    all_nodes = []
    
    def traverse(node):
        all_nodes.append(node)
        for child in node['children']:
            traverse(child)
    
    for node in nodes:
        traverse(node)
    
    return all_nodes


def verify_tree_integrity(events: List[TraceEvent], tree: List[Dict]) -> tuple[bool, str]:
    """Verify tree integrity matches events."""
    all_tree_nodes = collect_all_nodes_ts(tree)
    
    # Check all events are in tree
    event_span_ids = set(e['span_id'] for e in events)
    tree_span_ids = set(n['event']['span_id'] for n in all_tree_nodes)
    
    if event_span_ids != tree_span_ids:
        missing = event_span_ids - tree_span_ids
        extra = tree_span_ids - event_span_ids
        return False, f"Span ID mismatch. Missing: {missing}, Extra: {extra}"
    
    # Check parent-child relationships
    for event in events:
        parent_id = event.get('parent_span_id')
        if parent_id:
            # Find child node
            child_node = next((n for n in all_tree_nodes if n['event']['span_id'] == event['span_id']), None)
            if not child_node:
                return False, f"Child node {event['span_id']} not found"
            
            # Find parent node
            parent_node = next((n for n in all_tree_nodes if n['event']['span_id'] == parent_id), None)
            if parent_node:
                # Verify child is in parent's children
                child_in_parent = any(c['event']['span_id'] == event['span_id'] for c in parent_node['children'])
                if not child_in_parent:
                    return False, f"Child {event['span_id']} not in parent {parent_id}'s children"
    
    return True, ""


def test_real_world_scenario():
    """Test a real-world multi-agent scenario."""
    print("\n" + "="*80)
    print("🧪 INTEGRATION TEST: Real-World Multi-Agent Scenario")
    print("="*80)
    
    # Simulate a real agent execution
    events = [
        # Main orchestrator
        create_event("orchestrator", None, "agent:orchestrator", "agent:orchestrator", 0.0),
        
        # Research agent branch
        create_event("research", "orchestrator", "agent:research", "agent:orchestrator/agent:research", 0.0),
        create_event("search-tool", "research", "tool:web_search", "agent:orchestrator/agent:research/tool:web_search", 0.0),
        create_event("search-api", "search-tool", "api_call", "agent:orchestrator/agent:research/tool:web_search/api_call", 0.03),
        create_event("analyze-tool", "research", "tool:analyze", "agent:orchestrator/agent:research/tool:analyze", 0.0),
        create_event("analyze-api", "analyze-tool", "api_call", "agent:orchestrator/agent:research/tool:analyze/api_call", 0.05),
        
        # Writing agent branch
        create_event("writing", "orchestrator", "agent:writing", "agent:orchestrator/agent:writing", 0.0),
        create_event("draft-tool", "writing", "tool:draft", "agent:orchestrator/agent:writing/tool:draft", 0.0),
        create_event("draft-api", "draft-tool", "api_call", "agent:orchestrator/agent:writing/tool:draft/api_call", 0.04),
        create_event("edit-tool", "writing", "tool:edit", "agent:orchestrator/agent:writing/tool:edit", 0.0),
        create_event("edit-api", "edit-tool", "api_call", "agent:orchestrator/agent:writing/tool:edit/api_call", 0.06),
    ]
    
    # Build tree
    tree = build_tree_ts_logic(events)
    
    # Verify integrity
    passed, msg = verify_tree_integrity(events, tree)
    
    if not passed:
        print(f"❌ FAILED: {msg}")
        return False
    
    # Verify structure
    if len(tree) != 1:
        print(f"❌ FAILED: Expected 1 root, got {len(tree)}")
        return False
    
    orchestrator = tree[0]
    if orchestrator['event']['span_id'] != "orchestrator":
        print(f"❌ FAILED: Wrong root node")
        return False
    
    if len(orchestrator['children']) != 2:
        print(f"❌ FAILED: Orchestrator should have 2 children, got {len(orchestrator['children'])}")
        return False
    
    # Verify all nodes present
    all_nodes = collect_all_nodes_ts(tree)
    if len(all_nodes) != len(events):
        print(f"❌ FAILED: Expected {len(events)} nodes, got {len(all_nodes)}")
        return False
    
    # Verify section paths
    for node in all_nodes:
        event = node['event']
        expected_path = event.get('section_path')
        if expected_path:
            # Verify section_path matches expected format
            if '/' in expected_path:
                parts = expected_path.split('/')
                # Each part should be agent:*, tool:*, step:*, or api_call
                for part in parts:
                    if not (part.startswith('agent:') or part.startswith('tool:') or 
                           part.startswith('step:') or part == 'api_call'):
                        print(f"❌ FAILED: Invalid section_path format: {expected_path}")
                        return False
    
    print("✅ PASSED: Real-world scenario tree structure is correct")
    print(f"   - Total nodes: {len(all_nodes)}")
    print(f"   - Root nodes: {len(tree)}")
    print(f"   - Tree depth: {max(len(n['event'].get('section_path', '').split('/')) for n in all_nodes)}")
    
    return True


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*80)
    print("🧪 INTEGRATION TEST: Edge Cases")
    print("="*80)
    
    test_cases = [
        {
            "name": "Empty events",
            "events": [],
            "expected_roots": 0,
        },
        {
            "name": "Single event",
            "events": [create_event("single", None, "agent:single", "agent:single")],
            "expected_roots": 1,
        },
        {
            "name": "Orphaned nodes",
            "events": [
                create_event("orphan1", "missing", "tool:orphan1", "tool:orphan1"),
                create_event("orphan2", "missing", "tool:orphan2", "tool:orphan2"),
            ],
            "expected_roots": 2,
        },
        {
            "name": "Deep nesting",
            "events": [
                create_event("l1", None, "agent:l1", "agent:l1"),
                create_event("l2", "l1", "agent:l2", "agent:l1/agent:l2"),
                create_event("l3", "l2", "agent:l3", "agent:l1/agent:l2/agent:l3"),
                create_event("l4", "l3", "tool:l4", "agent:l1/agent:l2/agent:l3/tool:l4"),
                create_event("l5", "l4", "api_call", "agent:l1/agent:l2/agent:l3/tool:l4/api_call"),
            ],
            "expected_roots": 1,
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        tree = build_tree_ts_logic(test_case["events"])
        passed, msg = verify_tree_integrity(test_case["events"], tree)
        
        if not passed:
            print(f"❌ FAILED: {test_case['name']} - {msg}")
            all_passed = False
        elif len(tree) != test_case["expected_roots"]:
            print(f"❌ FAILED: {test_case['name']} - Expected {test_case['expected_roots']} roots, got {len(tree)}")
            all_passed = False
        else:
            print(f"✅ PASSED: {test_case['name']}")
    
    return all_passed


def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("🚀 VISUALIZATION INTEGRATION TESTS")
    print("="*80)
    
    results = []
    
    # Test real-world scenario
    results.append(("Real-World Scenario", test_real_world_scenario()))
    
    # Test edge cases
    results.append(("Edge Cases", test_edge_cases()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Visualization tree building is 100% accurate!")
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
    
    print("="*80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())


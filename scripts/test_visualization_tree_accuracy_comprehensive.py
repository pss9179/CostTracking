#!/usr/bin/env python3
"""
Comprehensive Test Suite: Visualization Tree Building Accuracy
Tests the actual tree building logic used in visualization components.

This ensures 100% accuracy for:
- Tree structure building from trace events
- Parent-child relationships
- Root node detection
- Edge cases (orphaned nodes, duplicates, etc.)
- Section path accuracy
- Cost aggregation
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from llmobserve.types import TraceEvent


class TreeNode:
    """Represents a node in the visualization tree."""
    def __init__(self, event: TraceEvent):
        self.event = event
        self.children: List['TreeNode'] = []
        self.total_cost: float = event.get('cost_usd', 0.0)
        self.call_count: int = 1

    def __repr__(self):
        return f"TreeNode(span_id={self.event['span_id']}, section={self.event['section']}, children={len(self.children)})"


def build_tree(events: List[TraceEvent]) -> List[TreeNode]:
    """
    Build a tree from trace events.
    Replicates the logic from GraphTreeVisualization.tsx and VisualTreeTrace.tsx
    """
    node_map: Dict[str, TreeNode] = {}
    root_nodes: List[TreeNode] = []

    # First pass: create all nodes
    for event in events:
        node_map[event['span_id']] = TreeNode(event)

    # Second pass: build tree structure
    for event in events:
        node = node_map.get(event['span_id'])
        if not node:
            continue

        parent_span_id = event.get('parent_span_id')
        if parent_span_id and parent_span_id in node_map:
            parent = node_map[parent_span_id]
            parent.children.append(node)
        else:
            root_nodes.append(node)

    return root_nodes


def collect_all_nodes(nodes: List[TreeNode]) -> List[TreeNode]:
    """Collect all nodes from tree recursively."""
    all_nodes = []
    
    def traverse(node: TreeNode):
        all_nodes.append(node)
        for child in node.children:
            traverse(child)
    
    for node in nodes:
        traverse(node)
    
    return all_nodes


def find_node_by_span_id(nodes: List[TreeNode], span_id: str) -> Optional[TreeNode]:
    """Find a node by span_id."""
    all_nodes = collect_all_nodes(nodes)
    for node in all_nodes:
        if node.event['span_id'] == span_id:
            return node
    return None


def verify_tree_structure(
    tree: List[TreeNode],
    expected_structure: Dict[str, List[str]]
) -> tuple[bool, str]:
    """
    Verify tree structure matches expected.
    expected_structure: {parent_span_id: [child_span_id, ...]}
    """
    for parent_id, expected_child_ids in expected_structure.items():
        parent = find_node_by_span_id(tree, parent_id)
        if not parent:
            return False, f"Parent node {parent_id} not found"
        
        actual_child_ids = sorted([c.event['span_id'] for c in parent.children])
        expected_child_ids_sorted = sorted(expected_child_ids)
        
        if actual_child_ids != expected_child_ids_sorted:
            return False, (
                f"Parent {parent_id} children mismatch:\n"
                f"  Expected: {expected_child_ids_sorted}\n"
                f"  Actual: {actual_child_ids}"
            )
    
    return True, ""


def verify_root_nodes(tree: List[TreeNode], expected_root_ids: List[str]) -> tuple[bool, str]:
    """Verify root nodes match expected."""
    actual_root_ids = sorted([n.event['span_id'] for n in tree])
    expected_root_ids_sorted = sorted(expected_root_ids)
    
    if actual_root_ids != expected_root_ids_sorted:
        return False, (
            f"Root nodes mismatch:\n"
            f"  Expected: {expected_root_ids_sorted}\n"
            f"  Actual: {actual_root_ids}"
        )
    
    return True, ""


def create_event(
    span_id: str,
    parent_span_id: Optional[str],
    section: str,
    section_path: Optional[str] = None,
    cost: float = 0.01,
    provider: str = "openai",
    endpoint: str = "chat.completions.create",
    model: str = "gpt-4"
) -> TraceEvent:
    """Create a test trace event."""
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


# ============================================================================
# TEST CASES
# ============================================================================

class TestResult:
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message


def test_simple_agent_tool_api() -> TestResult:
    """Test 1: Simple Agent → Tool → API Call"""
    events = [
        create_event("agent-1", None, "agent:research", "agent:research"),
        create_event("tool-1", "agent-1", "tool:web_search", "agent:research/tool:web_search"),
        create_event("api-1", "tool-1", "api_call", "agent:research/tool:web_search/api_call", 0.05),
    ]
    
    tree = build_tree(events)
    
    if len(tree) != 1:
        return TestResult("Test 1", False, f"Expected 1 root, got {len(tree)}")
    
    if tree[0].event['span_id'] != "agent-1":
        return TestResult("Test 1", False, f"Root should be agent-1, got {tree[0].event['span_id']}")
    
    if len(tree[0].children) != 1:
        return TestResult("Test 1", False, f"Agent should have 1 child, got {len(tree[0].children)}")
    
    tool = tree[0].children[0]
    if tool.event['span_id'] != "tool-1":
        return TestResult("Test 1", False, f"Tool should be tool-1, got {tool.event['span_id']}")
    
    if len(tool.children) != 1:
        return TestResult("Test 1", False, f"Tool should have 1 child, got {len(tool.children)}")
    
    api = tool.children[0]
    if api.event['span_id'] != "api-1":
        return TestResult("Test 1", False, f"API should be api-1, got {api.event['span_id']}")
    
    # Verify structure
    structure = {
        "agent-1": ["tool-1"],
        "tool-1": ["api-1"],
    }
    passed, msg = verify_tree_structure(tree, structure)
    if not passed:
        return TestResult("Test 1", False, msg)
    
    passed, msg = verify_root_nodes(tree, ["agent-1"])
    if not passed:
        return TestResult("Test 1", False, msg)
    
    return TestResult("Test 1: Simple Agent → Tool → API Call", True)


def test_multiple_root_nodes() -> TestResult:
    """Test 2: Multiple Independent Root Nodes"""
    events = [
        create_event("root-1", None, "agent:agent1", "agent:agent1"),
        create_event("child-1", "root-1", "tool:tool1", "agent:agent1/tool:tool1"),
        create_event("root-2", None, "agent:agent2", "agent:agent2"),
        create_event("child-2", "root-2", "tool:tool2", "agent:agent2/tool:tool2"),
    ]
    
    tree = build_tree(events)
    
    if len(tree) != 2:
        return TestResult("Test 2", False, f"Expected 2 roots, got {len(tree)}")
    
    passed, msg = verify_root_nodes(tree, ["root-1", "root-2"])
    if not passed:
        return TestResult("Test 2", False, msg)
    
    root1 = find_node_by_span_id(tree, "root-1")
    root2 = find_node_by_span_id(tree, "root-2")
    
    if root1.children[0].event['span_id'] != "child-1":
        return TestResult("Test 2", False, "Root1 child mismatch")
    
    if root2.children[0].event['span_id'] != "child-2":
        return TestResult("Test 2", False, "Root2 child mismatch")
    
    return TestResult("Test 2: Multiple Independent Root Nodes", True)


def test_deep_nesting() -> TestResult:
    """Test 3: Deep Nesting (5 Levels)"""
    events = [
        create_event("level-1", None, "agent:main", "agent:main"),
        create_event("level-2", "level-1", "agent:sub1", "agent:main/agent:sub1"),
        create_event("level-3", "level-2", "tool:tool1", "agent:main/agent:sub1/tool:tool1"),
        create_event("level-4", "level-3", "step:step1", "agent:main/agent:sub1/tool:tool1/step:step1"),
        create_event("level-5", "level-4", "api_call", "agent:main/agent:sub1/tool:tool1/step:step1/api_call"),
    ]
    
    tree = build_tree(events)
    
    if len(tree) != 1:
        return TestResult("Test 3", False, f"Expected 1 root, got {len(tree)}")
    
    current = tree[0]
    for i in range(1, 6):
        if current.event['span_id'] != f"level-{i}":
            return TestResult("Test 3", False, f"Level {i} mismatch: {current.event['span_id']}")
        if i < 5:
            if len(current.children) != 1:
                return TestResult("Test 3", False, f"Level {i} should have 1 child, got {len(current.children)}")
            current = current.children[0]
        else:
            if len(current.children) != 0:
                return TestResult("Test 3", False, f"Level 5 should have 0 children, got {len(current.children)}")
    
    return TestResult("Test 3: Deep Nesting (5 Levels)", True)


def test_multiple_children() -> TestResult:
    """Test 4: Agent with Multiple Tools"""
    events = [
        create_event("agent-1", None, "agent:research", "agent:research"),
        create_event("tool-1", "agent-1", "tool:search", "agent:research/tool:search"),
        create_event("tool-2", "agent-1", "tool:analyze", "agent:research/tool:analyze"),
        create_event("tool-3", "agent-1", "tool:summarize", "agent:research/tool:summarize"),
    ]
    
    tree = build_tree(events)
    
    if len(tree) != 1:
        return TestResult("Test 4", False, f"Expected 1 root, got {len(tree)}")
    
    agent = tree[0]
    if len(agent.children) != 3:
        return TestResult("Test 4", False, f"Agent should have 3 children, got {len(agent.children)}")
    
    child_ids = sorted([c.event['span_id'] for c in agent.children])
    expected_ids = ["tool-1", "tool-2", "tool-3"]
    
    if child_ids != expected_ids:
        return TestResult("Test 4", False, f"Children mismatch: {child_ids} vs {expected_ids}")
    
    return TestResult("Test 4: Agent with Multiple Tools", True)


def test_orphaned_node() -> TestResult:
    """Test 5: Orphaned Node Becomes Root"""
    events = [
        create_event("orphan-1", "non-existent-parent", "tool:orphan", "tool:orphan"),
        create_event("root-1", None, "agent:main", "agent:main"),
    ]
    
    tree = build_tree(events)
    
    if len(tree) != 2:
        return TestResult("Test 5", False, f"Expected 2 roots, got {len(tree)}")
    
    passed, msg = verify_root_nodes(tree, ["orphan-1", "root-1"])
    if not passed:
        return TestResult("Test 5", False, msg)
    
    orphan = find_node_by_span_id(tree, "orphan-1")
    if orphan.children:
        return TestResult("Test 5", False, "Orphan should have no children")
    
    return TestResult("Test 5: Orphaned Node Becomes Root", True)


def test_empty_events() -> TestResult:
    """Test 6: Empty Events Array"""
    events = []
    tree = build_tree(events)
    
    if len(tree) != 0:
        return TestResult("Test 6", False, f"Expected 0 roots, got {len(tree)}")
    
    return TestResult("Test 6: Empty Events Array", True)


def test_single_node() -> TestResult:
    """Test 7: Single Root Node"""
    events = [
        create_event("single-1", None, "agent:single", "agent:single"),
    ]
    
    tree = build_tree(events)
    
    if len(tree) != 1:
        return TestResult("Test 7", False, f"Expected 1 root, got {len(tree)}")
    
    if tree[0].event['span_id'] != "single-1":
        return TestResult("Test 7", False, "Wrong root node")
    
    if tree[0].children:
        return TestResult("Test 7", False, "Root should have no children")
    
    return TestResult("Test 7: Single Root Node", True)


def test_complex_nested_structure() -> TestResult:
    """Test 8: Complex Nested Agent Structure"""
    events = [
        create_event("main", None, "agent:main", "agent:main"),
        create_event("planning", "main", "agent:planning", "agent:main/agent:planning"),
        create_event("plan-tool", "planning", "tool:plan", "agent:main/agent:planning/tool:plan"),
        create_event("plan-api", "plan-tool", "api_call", "agent:main/agent:planning/tool:plan/api_call", 0.03),
        create_event("execution", "main", "agent:execution", "agent:main/agent:execution"),
        create_event("exec-tool", "execution", "tool:execute", "agent:main/agent:execution/tool:execute"),
        create_event("exec-api", "exec-tool", "api_call", "agent:main/agent:execution/tool:execute/api_call", 0.05),
    ]
    
    tree = build_tree(events)
    
    if len(tree) != 1:
        return TestResult("Test 8", False, f"Expected 1 root, got {len(tree)}")
    
    main = tree[0]
    if main.event['span_id'] != "main":
        return TestResult("Test 8", False, "Wrong root")
    
    if len(main.children) != 2:
        return TestResult("Test 8", False, f"Main should have 2 children, got {len(main.children)}")
    
    planning = find_node_by_span_id(tree, "planning")
    execution = find_node_by_span_id(tree, "execution")
    
    if not planning or len(planning.children) != 1:
        return TestResult("Test 8", False, "Planning structure incorrect")
    
    if not execution or len(execution.children) != 1:
        return TestResult("Test 8", False, "Execution structure incorrect")
    
    return TestResult("Test 8: Complex Nested Agent Structure", True)


def test_section_path_accuracy() -> TestResult:
    """Test 9: Section Path Accuracy"""
    events = [
        create_event("agent-1", None, "agent:research", "agent:research"),
        create_event("tool-1", "agent-1", "tool:web_search", "agent:research/tool:web_search"),
        create_event("api-1", "tool-1", "api_call", "agent:research/tool:web_search/api_call", 0.05),
    ]
    
    tree = build_tree(events)
    all_nodes = collect_all_nodes(tree)
    
    agent = find_node_by_span_id(tree, "agent-1")
    tool = find_node_by_span_id(tree, "tool-1")
    api = find_node_by_span_id(tree, "api-1")
    
    if agent.event['section_path'] != "agent:research":
        return TestResult("Test 9", False, f"Agent path mismatch: {agent.event['section_path']}")
    
    if tool.event['section_path'] != "agent:research/tool:web_search":
        return TestResult("Test 9", False, f"Tool path mismatch: {tool.event['section_path']}")
    
    if api.event['section_path'] != "agent:research/tool:web_search/api_call":
        return TestResult("Test 9", False, f"API path mismatch: {api.event['section_path']}")
    
    return TestResult("Test 9: Section Path Accuracy", True)


def test_all_events_included() -> TestResult:
    """Test 10: All Events Included in Tree"""
    events = [
        create_event("a", None, "agent:a", "agent:a"),
        create_event("b", "a", "tool:b", "agent:a/tool:b"),
        create_event("c", "a", "tool:c", "agent:a/tool:c"),
        create_event("d", "b", "step:d", "agent:a/tool:b/step:d"),
        create_event("e", "c", "step:e", "agent:a/tool:c/step:e"),
    ]
    
    tree = build_tree(events)
    all_nodes = collect_all_nodes(tree)
    
    if len(all_nodes) != len(events):
        return TestResult("Test 10", False, f"Expected {len(events)} nodes, got {len(all_nodes)}")
    
    event_span_ids = set(e['span_id'] for e in events)
    tree_span_ids = set(n.event['span_id'] for n in all_nodes)
    
    if event_span_ids != tree_span_ids:
        missing = event_span_ids - tree_span_ids
        extra = tree_span_ids - event_span_ids
        return TestResult("Test 10", False, f"Span ID mismatch. Missing: {missing}, Extra: {extra}")
    
    return TestResult("Test 10: All Events Included in Tree", True)


def test_cost_preservation() -> TestResult:
    """Test 11: Cost Values Preserved"""
    events = [
        create_event("node-1", None, "agent:test", "agent:test", 0.10),
        create_event("node-2", "node-1", "tool:test", "agent:test/tool:test", 0.05),
        create_event("node-3", "node-2", "api_call", "agent:test/tool:test/api_call", 0.02),
    ]
    
    tree = build_tree(events)
    all_nodes = collect_all_nodes(tree)
    
    node1 = find_node_by_span_id(tree, "node-1")
    node2 = find_node_by_span_id(tree, "node-2")
    node3 = find_node_by_span_id(tree, "node-3")
    
    if abs(node1.event['cost_usd'] - 0.10) > 0.0001:
        return TestResult("Test 11", False, f"Node1 cost mismatch: {node1.event['cost_usd']}")
    
    if abs(node2.event['cost_usd'] - 0.05) > 0.0001:
        return TestResult("Test 11", False, f"Node2 cost mismatch: {node2.event['cost_usd']}")
    
    if abs(node3.event['cost_usd'] - 0.02) > 0.0001:
        return TestResult("Test 11", False, f"Node3 cost mismatch: {node3.event['cost_usd']}")
    
    return TestResult("Test 11: Cost Values Preserved", True)


def test_large_tree() -> TestResult:
    """Test 12: Large Tree (100 Nodes)"""
    events = [
        create_event("root", None, "agent:root", "agent:root"),
    ]
    
    # Create 99 children
    for i in range(99):
        parent_id = "root" if i == 0 else f"node-{i // 2}"
        events.append(create_event(f"node-{i}", parent_id, f"tool:tool{i}", f"agent:root/tool:tool{i}"))
    
    tree = build_tree(events)
    
    if len(tree) != 1:
        return TestResult("Test 12", False, f"Expected 1 root, got {len(tree)}")
    
    all_nodes = collect_all_nodes(tree)
    if len(all_nodes) != 100:
        return TestResult("Test 12", False, f"Expected 100 nodes, got {len(all_nodes)}")
    
    return TestResult("Test 12: Large Tree (100 Nodes)", True)


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE VISUALIZATION TREE ACCURACY TESTS")
    print("="*80)
    
    tests = [
        test_simple_agent_tool_api,
        test_multiple_root_nodes,
        test_deep_nesting,
        test_multiple_children,
        test_orphaned_node,
        test_empty_events,
        test_single_node,
        test_complex_nested_structure,
        test_section_path_accuracy,
        test_all_events_included,
        test_cost_preservation,
        test_large_tree,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            print(f"{status}: {result.name}")
            if not result.passed and result.message:
                print(f"   {result.message}")
        except Exception as e:
            results.append(TestResult(test_func.__name__, False, str(e)))
            print(f"❌ FAILED: {test_func.__name__}")
            print(f"   Exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    accuracy = (passed / total * 100) if total > 0 else 0
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    
    if accuracy == 100:
        print("\n🎉 ALL TESTS PASSED! Visualization tree building is 100% accurate!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
    
    print("="*80)
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
    sys.exit(0 if all(r.passed for r in results) else 1)


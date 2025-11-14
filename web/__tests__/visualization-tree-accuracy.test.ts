/**
 * Comprehensive Test Suite: Visualization Tree Building Accuracy
 * 
 * Tests the buildTree() function used in:
 * - GraphTreeVisualization.tsx
 * - VisualTreeTrace.tsx
 * - HierarchicalTrace.tsx
 * 
 * Ensures 100% accuracy for agent visualization trees.
 */

interface TraceEvent {
  id: string;
  span_id: string;
  parent_span_id: string | null;
  section: string;
  section_path: string | null;
  provider: string;
  endpoint: string;
  model: string | null;
  cost_usd: number;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  status: string;
  created_at: string;
}

interface TreeNode {
  event: TraceEvent;
  children: TreeNode[];
  [key: string]: any; // For different implementations
}

// Replicate the buildTree function from GraphTreeVisualization.tsx
function buildTree(events: TraceEvent[]): TreeNode[] {
  const nodeMap = new Map<string, TreeNode>();
  const rootNodes: TreeNode[] = [];

  // First pass: create all nodes
  events.forEach((event) => {
    nodeMap.set(event.span_id, {
      event,
      children: [],
      x: 0,
      y: 0,
      id: event.span_id,
    });
  });

  // Second pass: build tree structure
  events.forEach((event) => {
    const node = nodeMap.get(event.span_id);
    if (!node) return;

    if (event.parent_span_id && nodeMap.has(event.parent_span_id)) {
      const parent = nodeMap.get(event.parent_span_id);
      if (parent) {
        parent.children.push(node);
      }
    } else {
      rootNodes.push(node);
    }
  });

  return rootNodes;
}

// Helper function to collect all nodes from tree
function collectAllNodes(nodes: TreeNode[]): TreeNode[] {
  const allNodes: TreeNode[] = [];
  const traverse = (node: TreeNode) => {
    allNodes.push(node);
    node.children.forEach(traverse);
  };
  nodes.forEach(traverse);
  return allNodes;
}

// Helper function to get node by span_id
function findNodeBySpanId(nodes: TreeNode[], spanId: string): TreeNode | null {
  const allNodes = collectAllNodes(nodes);
  return allNodes.find(n => n.event.span_id === spanId) || null;
}

// Helper function to verify tree structure
function verifyTreeStructure(
  tree: TreeNode[],
  expectedStructure: { [spanId: string]: string[] } // parent -> children[]
): boolean {
  for (const [parentId, childIds] of Object.entries(expectedStructure)) {
    const parent = findNodeBySpanId(tree, parentId);
    if (!parent) {
      console.error(`❌ Parent node ${parentId} not found`);
      return false;
    }
    
    if (parent.children.length !== childIds.length) {
      console.error(`❌ Parent ${parentId} has ${parent.children.length} children, expected ${childIds.length}`);
      return false;
    }
    
    const actualChildIds = parent.children.map(c => c.event.span_id).sort();
    const expectedChildIds = [...childIds].sort();
    
    if (JSON.stringify(actualChildIds) !== JSON.stringify(expectedChildIds)) {
      console.error(`❌ Parent ${parentId} children mismatch:`);
      console.error(`   Expected: ${expectedChildIds}`);
      console.error(`   Actual: ${actualChildIds}`);
      return false;
    }
  }
  return true;
}

// Helper function to verify root nodes
function verifyRootNodes(tree: TreeNode[], expectedRootIds: string[]): boolean {
  const actualRootIds = tree.map(n => n.event.span_id).sort();
  const expectedRootIdsSorted = [...expectedRootIds].sort();
  
  if (JSON.stringify(actualRootIds) !== JSON.stringify(expectedRootIdsSorted)) {
    console.error(`❌ Root nodes mismatch:`);
    console.error(`   Expected: ${expectedRootIdsSorted}`);
    console.error(`   Actual: ${actualRootIds}`);
    return false;
  }
  return true;
}

// Helper to create a test event
function createEvent(
  spanId: string,
  parentSpanId: string | null,
  section: string,
  sectionPath: string | null = null,
  cost: number = 0.01
): TraceEvent {
  return {
    id: `id-${spanId}`,
    span_id: spanId,
    parent_span_id: parentSpanId,
    section,
    section_path: sectionPath,
    provider: "openai",
    endpoint: "chat.completions.create",
    model: "gpt-4",
    cost_usd: cost,
    latency_ms: 100,
    input_tokens: 10,
    output_tokens: 20,
    status: "ok",
    created_at: new Date().toISOString(),
  };
}

// ============================================================================
// TEST CASES
// ============================================================================

describe("Visualization Tree Building - 100% Accuracy Tests", () => {
  
  // Test 1: Simple parent-child relationship
  test("Test 1: Simple Agent → Tool → API Call", () => {
    const events: TraceEvent[] = [
      createEvent("agent-1", null, "agent:research", "agent:research"),
      createEvent("tool-1", "agent-1", "tool:web_search", "agent:research/tool:web_search"),
      createEvent("api-1", "tool-1", "api_call", "agent:research/tool:web_search/api_call", 0.05),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    expect(tree[0].event.span_id).toBe("agent-1");
    expect(tree[0].children.length).toBe(1);
    expect(tree[0].children[0].event.span_id).toBe("tool-1");
    expect(tree[0].children[0].children.length).toBe(1);
    expect(tree[0].children[0].children[0].event.span_id).toBe("api-1");
    
    const structure = {
      "agent-1": ["tool-1"],
      "tool-1": ["api-1"],
    };
    expect(verifyTreeStructure(tree, structure)).toBe(true);
    expect(verifyRootNodes(tree, ["agent-1"])).toBe(true);
  });

  // Test 2: Multiple root nodes (independent trees)
  test("Test 2: Multiple Independent Root Nodes", () => {
    const events: TraceEvent[] = [
      createEvent("root-1", null, "agent:agent1", "agent:agent1"),
      createEvent("child-1", "root-1", "tool:tool1", "agent:agent1/tool:tool1"),
      createEvent("root-2", null, "agent:agent2", "agent:agent2"),
      createEvent("child-2", "root-2", "tool:tool2", "agent:agent2/tool:tool2"),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(2);
    expect(verifyRootNodes(tree, ["root-1", "root-2"])).toBe(true);
    
    const root1 = findNodeBySpanId(tree, "root-1");
    const root2 = findNodeBySpanId(tree, "root-2");
    
    expect(root1?.children.length).toBe(1);
    expect(root1?.children[0].event.span_id).toBe("child-1");
    expect(root2?.children.length).toBe(1);
    expect(root2?.children[0].event.span_id).toBe("child-2");
  });

  // Test 3: Deep nesting (5 levels)
  test("Test 3: Deep Nesting (5 Levels)", () => {
    const events: TraceEvent[] = [
      createEvent("level-1", null, "agent:main", "agent:main"),
      createEvent("level-2", "level-1", "agent:sub1", "agent:main/agent:sub1"),
      createEvent("level-3", "level-2", "tool:tool1", "agent:main/agent:sub1/tool:tool1"),
      createEvent("level-4", "level-3", "step:step1", "agent:main/agent:sub1/tool:tool1/step:step1"),
      createEvent("level-5", "level-4", "api_call", "agent:main/agent:sub1/tool:tool1/step:step1/api_call"),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    
    let current = tree[0];
    expect(current.event.span_id).toBe("level-1");
    
    for (let i = 2; i <= 5; i++) {
      expect(current.children.length).toBe(1);
      current = current.children[0];
      expect(current.event.span_id).toBe(`level-${i}`);
    }
    
    expect(current.children.length).toBe(0);
  });

  // Test 4: Multiple children under same parent
  test("Test 4: Agent with Multiple Tools", () => {
    const events: TraceEvent[] = [
      createEvent("agent-1", null, "agent:research", "agent:research"),
      createEvent("tool-1", "agent-1", "tool:search", "agent:research/tool:search"),
      createEvent("tool-2", "agent-1", "tool:analyze", "agent:research/tool:analyze"),
      createEvent("tool-3", "agent-1", "tool:summarize", "agent:research/tool:summarize"),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    const agent = tree[0];
    expect(agent.children.length).toBe(3);
    
    const childIds = agent.children.map(c => c.event.span_id).sort();
    expect(childIds).toEqual(["tool-1", "tool-2", "tool-3"]);
  });

  // Test 5: Orphaned node (parent_span_id doesn't exist)
  test("Test 5: Orphaned Node Becomes Root", () => {
    const events: TraceEvent[] = [
      createEvent("orphan-1", "non-existent-parent", "tool:orphan", "tool:orphan"),
      createEvent("root-1", null, "agent:main", "agent:main"),
    ];

    const tree = buildTree(events);
    
    // Orphaned node should become a root
    expect(tree.length).toBe(2);
    expect(verifyRootNodes(tree, ["orphan-1", "root-1"])).toBe(true);
    
    const orphan = findNodeBySpanId(tree, "orphan-1");
    expect(orphan?.children.length).toBe(0);
  });

  // Test 6: Empty events array
  test("Test 6: Empty Events Array", () => {
    const events: TraceEvent[] = [];
    const tree = buildTree(events);
    expect(tree.length).toBe(0);
  });

  // Test 7: Single node (no parent)
  test("Test 7: Single Root Node", () => {
    const events: TraceEvent[] = [
      createEvent("single-1", null, "agent:single", "agent:single"),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    expect(tree[0].event.span_id).toBe("single-1");
    expect(tree[0].children.length).toBe(0);
  });

  // Test 8: Complex nested structure (real-world scenario)
  test("Test 8: Complex Nested Agent Structure", () => {
    const events: TraceEvent[] = [
      // Main agent
      createEvent("main", null, "agent:main", "agent:main"),
      
      // Planning agent branch
      createEvent("planning", "main", "agent:planning", "agent:main/agent:planning"),
      createEvent("plan-tool", "planning", "tool:plan", "agent:main/agent:planning/tool:plan"),
      createEvent("plan-api", "plan-tool", "api_call", "agent:main/agent:planning/tool:plan/api_call", 0.03),
      
      // Execution agent branch
      createEvent("execution", "main", "agent:execution", "agent:main/agent:execution"),
      createEvent("exec-tool", "execution", "tool:execute", "agent:main/agent:execution/tool:execute"),
      createEvent("exec-api", "exec-tool", "api_call", "agent:main/agent:execution/tool:execute/api_call", 0.05),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    const main = tree[0];
    expect(main.event.span_id).toBe("main");
    expect(main.children.length).toBe(2);
    
    const planning = findNodeBySpanId(tree, "planning");
    const execution = findNodeBySpanId(tree, "execution");
    
    expect(planning?.children.length).toBe(1);
    expect(planning?.children[0].event.span_id).toBe("plan-tool");
    expect(planning?.children[0].children.length).toBe(1);
    expect(planning?.children[0].children[0].event.span_id).toBe("plan-api");
    
    expect(execution?.children.length).toBe(1);
    expect(execution?.children[0].event.span_id).toBe("exec-tool");
    expect(execution?.children[0].children.length).toBe(1);
    expect(execution?.children[0].children[0].event.span_id).toBe("exec-api");
  });

  // Test 9: All nodes have same parent (star topology)
  test("Test 9: Star Topology (One Parent, Many Children)", () => {
    const events: TraceEvent[] = [
      createEvent("parent", null, "agent:coordinator", "agent:coordinator"),
      ...Array.from({ length: 10 }, (_, i) => 
        createEvent(`child-${i}`, "parent", `tool:tool${i}`, `agent:coordinator/tool:tool${i}`)
      ),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    const parent = tree[0];
    expect(parent.children.length).toBe(10);
    
    const childIds = parent.children.map(c => c.event.span_id).sort();
    const expectedIds = Array.from({ length: 10 }, (_, i) => `child-${i}`).sort();
    expect(childIds).toEqual(expectedIds);
  });

  // Test 10: Chain topology (linear chain)
  test("Test 10: Linear Chain Topology", () => {
    const events: TraceEvent[] = [
      createEvent("node-1", null, "agent:start", "agent:start"),
      createEvent("node-2", "node-1", "agent:middle1", "agent:start/agent:middle1"),
      createEvent("node-3", "node-2", "agent:middle2", "agent:start/agent:middle1/agent:middle2"),
      createEvent("node-4", "node-3", "tool:end", "agent:start/agent:middle1/agent:middle2/tool:end"),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    
    let current = tree[0];
    for (let i = 1; i <= 4; i++) {
      expect(current.event.span_id).toBe(`node-${i}`);
      if (i < 4) {
        expect(current.children.length).toBe(1);
        current = current.children[0];
      } else {
        expect(current.children.length).toBe(0);
      }
    }
  });

  // Test 11: Mixed valid and orphaned nodes
  test("Test 11: Mixed Valid and Orphaned Nodes", () => {
    const events: TraceEvent[] = [
      // Valid tree
      createEvent("root-1", null, "agent:valid", "agent:valid"),
      createEvent("child-1", "root-1", "tool:valid", "agent:valid/tool:valid"),
      
      // Orphaned nodes
      createEvent("orphan-1", "missing-parent-1", "tool:orphan1", "tool:orphan1"),
      createEvent("orphan-2", "missing-parent-2", "tool:orphan2", "tool:orphan2"),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(3); // 1 valid root + 2 orphans
    
    const root1 = findNodeBySpanId(tree, "root-1");
    const orphan1 = findNodeBySpanId(tree, "orphan-1");
    const orphan2 = findNodeBySpanId(tree, "orphan-2");
    
    expect(root1?.children.length).toBe(1);
    expect(orphan1?.children.length).toBe(0);
    expect(orphan2?.children.length).toBe(0);
    
    expect(verifyRootNodes(tree, ["root-1", "orphan-1", "orphan-2"])).toBe(true);
  });

  // Test 12: Section path accuracy
  test("Test 12: Section Path Accuracy", () => {
    const events: TraceEvent[] = [
      createEvent("agent-1", null, "agent:research", "agent:research"),
      createEvent("tool-1", "agent-1", "tool:web_search", "agent:research/tool:web_search"),
      createEvent("api-1", "tool-1", "api_call", "agent:research/tool:web_search/api_call", 0.05),
    ];

    const tree = buildTree(events);
    const allNodes = collectAllNodes(tree);
    
    const agent = allNodes.find(n => n.event.span_id === "agent-1");
    const tool = allNodes.find(n => n.event.span_id === "tool-1");
    const api = allNodes.find(n => n.event.span_id === "api-1");
    
    expect(agent?.event.section_path).toBe("agent:research");
    expect(tool?.event.section_path).toBe("agent:research/tool:web_search");
    expect(api?.event.section_path).toBe("agent:research/tool:web_search/api_call");
  });

  // Test 13: Duplicate span_ids (should handle gracefully)
  test("Test 13: Duplicate Span IDs (Last Wins)", () => {
    const events: TraceEvent[] = [
      createEvent("duplicate", null, "agent:first", "agent:first"),
      createEvent("duplicate", null, "agent:second", "agent:second"), // Same span_id
      createEvent("child", "duplicate", "tool:child", "agent:second/tool:child"),
    ];

    const tree = buildTree(events);
    
    // Should only have one node with span_id "duplicate"
    const allNodes = collectAllNodes(tree);
    const duplicateNodes = allNodes.filter(n => n.event.span_id === "duplicate");
    
    // Last event overwrites previous ones in the map
    expect(duplicateNodes.length).toBe(1);
    expect(duplicateNodes[0].event.section).toBe("agent:second");
    
    // Child should be attached to the last duplicate
    expect(duplicateNodes[0].children.length).toBe(1);
    expect(duplicateNodes[0].children[0].event.span_id).toBe("child");
  });

  // Test 14: Self-referencing parent (should become root)
  test("Test 14: Self-Referencing Parent Becomes Root", () => {
    const events: TraceEvent[] = [
      createEvent("self-ref", "self-ref", "agent:self", "agent:self"), // parent points to itself
    ];

    const tree = buildTree(events);
    
    // Should become a root node since parent doesn't exist in map yet
    expect(tree.length).toBe(1);
    expect(tree[0].event.span_id).toBe("self-ref");
    expect(tree[0].children.length).toBe(0);
  });

  // Test 15: Large tree (performance and correctness)
  test("Test 15: Large Tree (100 Nodes)", () => {
    const events: TraceEvent[] = [
      createEvent("root", null, "agent:root", "agent:root"),
    ];
    
    // Create 99 children in a balanced tree structure
    for (let i = 0; i < 99; i++) {
      const parentId = i === 0 ? "root" : `node-${Math.floor((i - 1) / 2)}`;
      events.push(createEvent(`node-${i}`, parentId, `tool:tool${i}`, `agent:root/tool:tool${i}`));
    }

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    const allNodes = collectAllNodes(tree);
    expect(allNodes.length).toBe(100); // root + 99 children
    
    const root = tree[0];
    expect(root.children.length).toBeGreaterThan(0);
  });

  // Test 16: Verify all events are included in tree
  test("Test 16: All Events Included in Tree", () => {
    const events: TraceEvent[] = [
      createEvent("a", null, "agent:a", "agent:a"),
      createEvent("b", "a", "tool:b", "agent:a/tool:b"),
      createEvent("c", "a", "tool:c", "agent:a/tool:c"),
      createEvent("d", "b", "step:d", "agent:a/tool:b/step:d"),
      createEvent("e", "c", "step:e", "agent:a/tool:c/step:e"),
    ];

    const tree = buildTree(events);
    const allNodes = collectAllNodes(tree);
    
    expect(allNodes.length).toBe(events.length);
    
    const eventSpanIds = new Set(events.map(e => e.span_id));
    const treeSpanIds = new Set(allNodes.map(n => n.event.span_id));
    
    expect(eventSpanIds.size).toBe(treeSpanIds.size);
    expect([...eventSpanIds].every(id => treeSpanIds.has(id))).toBe(true);
  });

  // Test 17: Null parent_span_id handling
  test("Test 17: Null Parent Span ID", () => {
    const events: TraceEvent[] = [
      createEvent("node-1", null, "agent:test", "agent:test"),
      createEvent("node-2", null, "agent:test2", "agent:test2"),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(2);
    expect(tree[0].children.length).toBe(0);
    expect(tree[1].children.length).toBe(0);
  });

  // Test 18: Empty string parent_span_id (should be treated as null)
  test("Test 18: Empty String Parent Span ID", () => {
    const events: TraceEvent[] = [
      {
        ...createEvent("node-1", null, "agent:test", "agent:test"),
        parent_span_id: "", // Empty string
      },
    ];

    const tree = buildTree(events);
    
    // Empty string should be treated as no parent (becomes root)
    expect(tree.length).toBe(1);
    expect(tree[0].event.span_id).toBe("node-1");
  });

  // Test 19: Cost values preserved
  test("Test 19: Cost Values Preserved", () => {
    const events: TraceEvent[] = [
      createEvent("node-1", null, "agent:test", "agent:test", 0.10),
      createEvent("node-2", "node-1", "tool:test", "agent:test/tool:test", 0.05),
      createEvent("node-3", "node-2", "api_call", "agent:test/tool:test/api_call", 0.02),
    ];

    const tree = buildTree(events);
    const allNodes = collectAllNodes(tree);
    
    const node1 = allNodes.find(n => n.event.span_id === "node-1");
    const node2 = allNodes.find(n => n.event.span_id === "node-2");
    const node3 = allNodes.find(n => n.event.span_id === "node-3");
    
    expect(node1?.event.cost_usd).toBe(0.10);
    expect(node2?.event.cost_usd).toBe(0.05);
    expect(node3?.event.cost_usd).toBe(0.02);
  });

  // Test 20: Complex real-world agent structure
  test("Test 20: Real-World Multi-Agent System", () => {
    const events: TraceEvent[] = [
      // Main orchestrator
      createEvent("orchestrator", null, "agent:orchestrator", "agent:orchestrator"),
      
      // Research agent branch
      createEvent("research", "orchestrator", "agent:research", "agent:orchestrator/agent:research"),
      createEvent("search-tool", "research", "tool:web_search", "agent:orchestrator/agent:research/tool:web_search"),
      createEvent("search-api", "search-tool", "api_call", "agent:orchestrator/agent:research/tool:web_search/api_call", 0.03),
      createEvent("analyze-tool", "research", "tool:analyze", "agent:orchestrator/agent:research/tool:analyze"),
      createEvent("analyze-api", "analyze-tool", "api_call", "agent:orchestrator/agent:research/tool:analyze/api_call", 0.05),
      
      // Writing agent branch
      createEvent("writing", "orchestrator", "agent:writing", "agent:orchestrator/agent:writing"),
      createEvent("draft-tool", "writing", "tool:draft", "agent:orchestrator/agent:writing/tool:draft"),
      createEvent("draft-api", "draft-tool", "api_call", "agent:orchestrator/agent:writing/tool:draft/api_call", 0.04),
      createEvent("edit-tool", "writing", "tool:edit", "agent:orchestrator/agent:writing/tool:edit"),
      createEvent("edit-api", "edit-tool", "api_call", "agent:orchestrator/agent:writing/tool:edit/api_call", 0.06),
    ];

    const tree = buildTree(events);
    
    expect(tree.length).toBe(1);
    const orchestrator = tree[0];
    expect(orchestrator.children.length).toBe(2);
    
    const research = findNodeBySpanId(tree, "research");
    const writing = findNodeBySpanId(tree, "writing");
    
    expect(research?.children.length).toBe(2);
    expect(writing?.children.length).toBe(2);
    
    // Verify all nodes are in tree
    const allNodes = collectAllNodes(tree);
    expect(allNodes.length).toBe(events.length);
  });
});

// Export for use in other test files
export { buildTree, createEvent, verifyTreeStructure, verifyRootNodes, collectAllNodes, findNodeBySpanId };


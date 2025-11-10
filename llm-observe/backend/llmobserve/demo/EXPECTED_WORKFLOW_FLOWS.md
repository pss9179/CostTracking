# Expected Workflow Flow Mappings

This document describes the expected trace structure for each complex workflow in `complex_nested_workflows.py`.

## Overview

Each workflow should create a separate trace with a root span named `workflow.<function_name>`. All API calls (GPT, Vapi, Google Calendar, Pinecone) should appear as child spans under their respective workflow root span.

---

## Workflow 1: `gpt_vapi_google_workflow`

**Sequence**: GPT → Vapi → GPT → Google Calendar

**Expected Trace Structure**:
```
workflow.gpt_vapi_google_workflow (root span)
  ├── llm.request (GPT: analyze call purpose)
  ├── vapi.create_call
  ├── vapi.get_call_status
  ├── llm.request (GPT: generate call summary)
  └── gcal.create_event
```

**Total Spans**: 6 (1 root + 5 children)

**Services Involved**: OpenAI, Vapi, Google Calendar

---

## Workflow 2: `vapi_google_pinecone_workflow`

**Sequence**: Vapi → Google Calendar → GPT → Pinecone → GPT

**Expected Trace Structure**:
```
workflow.vapi_google_pinecone_workflow (root span)
  ├── vapi.create_call
  ├── gcal.list_events
  ├── llm.request (GPT: generate search query)
  ├── pinecone.query
  └── llm.request (GPT: summarize results)
```

**Total Spans**: 6 (1 root + 5 children)

**Services Involved**: Vapi, Google Calendar, OpenAI, Pinecone

---

## Workflow 3: `nested_async_workflow` ⚠️ MOST COMPLEX

**Sequence**: GPT → [Nested: GPT+Vapi+Google] → [Nested: Vapi+Google+Pinecone] → GPT

**Expected Trace Structure**:
```
workflow.nested_async_workflow (root span)
  ├── llm.request (GPT: initial analysis)
  ├── workflow.gpt_vapi_google_workflow (nested workflow span)
  │   ├── llm.request (GPT: analyze call purpose)
  │   ├── vapi.create_call
  │   ├── vapi.get_call_status
  │   ├── llm.request (GPT: generate summary)
  │   └── gcal.create_event
  ├── workflow.vapi_google_pinecone_workflow (nested workflow span)
  │   ├── vapi.create_call
  │   ├── gcal.list_events
  │   ├── llm.request (GPT: generate search query)
  │   ├── pinecone.query
  │   └── llm.request (GPT: summarize results)
  └── llm.request (GPT: final synthesis)
```

**Total Spans**: 14 (1 root + 2 nested workflow spans + 11 API call spans)

**Services Involved**: OpenAI, Vapi, Google Calendar, Pinecone

**Key Test**: This verifies that nested workflows create their own workflow spans that are children of the parent workflow span.

---

## Workflow 4: `parallel_workflows_with_nesting`

**Sequence**: Parallel execution of workflows 1 & 2

**Expected Trace Structure**:
```
workflow.parallel_workflows_with_nesting (root span)
  ├── workflow.gpt_vapi_google_workflow (parallel task 1)
  │   ├── llm.request (GPT: analyze call purpose)
  │   ├── vapi.create_call
  │   ├── vapi.get_call_status
  │   ├── llm.request (GPT: generate summary)
  │   └── gcal.create_event
  └── workflow.vapi_google_pinecone_workflow (parallel task 2)
      ├── vapi.create_call
      ├── gcal.list_events
      ├── llm.request (GPT: generate search query)
      ├── pinecone.query
      └── llm.request (GPT: summarize results)
```

**Total Spans**: 13 (1 root + 2 nested workflow spans + 10 API call spans)

**Services Involved**: OpenAI, Vapi, Google Calendar, Pinecone

**Key Test**: This verifies that parallel async workflows both create their own workflow spans as children of the parent.

---

## Workflow 5: `deeply_nested_workflow` ⚠️ DEEPEST NESTING

**Sequence**: GPT → [Level 1 → [Level 2 → GPT+Vapi]] → Pinecone

**Expected Trace Structure**:
```
workflow.deeply_nested_workflow (root span)
  ├── llm.request (GPT: initial query)
  ├── workflow.helper_workflow_level_1 (nested level 1)
  │   ├── workflow.helper_workflow_level_2 (nested level 2)
  │   │   ├── llm.request (GPT: inner analysis)
  │   │   └── vapi.create_call
  │   └── gcal.create_event
  └── pinecone.query
```

**Total Spans**: 7 (1 root + 2 nested workflow spans + 4 API call spans)

**Services Involved**: OpenAI, Vapi, Google Calendar, Pinecone

**Key Test**: This verifies that deeply nested workflows (3 levels) all create proper workflow spans in a hierarchy.

---

## Summary Statistics

| Workflow | Total Spans | Nested Workflows | Services Used |
|----------|------------|------------------|---------------|
| 1. gpt_vapi_google_workflow | 6 | 0 | GPT, Vapi, Google |
| 2. vapi_google_pinecone_workflow | 6 | 0 | Vapi, Google, Pinecone, GPT |
| 3. nested_async_workflow | 14 | 2 | All |
| 4. parallel_workflows_with_nesting | 13 | 2 | All |
| 5. deeply_nested_workflow | 7 | 2 | GPT, Vapi, Google, Pinecone |

---

## How to Verify

1. **Run the workflows**:
   ```python
   from llmobserve.demo.complex_nested_workflows import run_all_complex_workflows
   import asyncio
   asyncio.run(run_all_complex_workflows())
   ```

2. **Check the UI**: Navigate to the tracing UI and verify:
   - Each workflow creates a separate trace (or appears as a workflow span)
   - Nested workflows appear as child spans of their parent workflow
   - All API calls appear as children of their respective workflow spans
   - Parallel workflows both appear as children of the parent

3. **Verify Span Hierarchy**:
   - Root spans should be named `workflow.<function_name>`
   - Nested workflow spans should be named `workflow.<nested_function_name>`
   - API call spans should be named according to their service (e.g., `llm.request`, `vapi.create_call`, etc.)

4. **Check Workflow Names**:
   - Each trace should have a `workflow_name` attribute extracted from the root span name
   - Nested workflows should maintain their own workflow context

---

## Potential Issues to Watch For

1. **Nested workflows not creating spans**: If nested workflows don't create their own workflow spans, they might be flattened into the parent workflow.

2. **Parallel workflows sharing context**: If parallel workflows share workflow context incorrectly, spans might be misattributed.

3. **Deep nesting breaking**: If the tracing system doesn't handle deep nesting, workflow spans might not be created at deeper levels.

4. **Async context propagation**: If async context doesn't propagate correctly, spans might not be associated with the right workflow.

---

## Expected Behavior

✅ **Correct**: Each `@workflow_trace` decorated function creates its own workflow span
✅ **Correct**: Nested workflows create workflow spans that are children of the parent workflow span
✅ **Correct**: All API calls within a workflow become children of that workflow's span
✅ **Correct**: Parallel workflows both create their own workflow spans as siblings under the parent

❌ **Incorrect**: Nested workflows flattening into parent (no separate workflow spans)
❌ **Incorrect**: API calls creating their own root spans instead of being children
❌ **Incorrect**: Parallel workflows sharing the same workflow span


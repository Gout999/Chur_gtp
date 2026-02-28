# Cognition Tool — Remaining Low-Severity Issues

These issues were identified during the critique of `tools/cognition.py` (Worklist Task #2).
They are acceptable for MVP but should be addressed before production.

---

## Issue #5: Timestamp inconsistency in `_archive_snapshot`

**File**: `tools/cognition.py` — `_archive_snapshot`

The function previously generated multiple `_utc_iso()` calls within a single invocation, producing slightly different timestamps. This was partially addressed in the medium-severity fix (now uses a single `now` variable), but any callers that chain multiple helpers should adopt the same pattern: capture one timestamp at the top and pass it through.

**Fix**: Audit all `_utc_iso()` call sites in the main `update_student_cognition_map` function body. Consider accepting a `now` parameter to ensure the entire update operation shares one timestamp.

---

## Issue #6: No rate-limiting on archive snapshots

**File**: `tools/cognition.py` — `_archive_snapshot`

Every call to `update_student_cognition_map` writes per-concept snapshot rows to `interaction_episodes`. A student with 100 interactions on 5 concepts produces 500 snapshot entries. This is fine for the in-memory `SharedMemoryClient` during development, but will be a scaling concern with real PostgreSQL/Redis.

**Fix options**:
- Only snapshot when confidence actually changed (skip if delta was clamped to zero).
- Snapshot at most once per N interactions (e.g., every 5th).
- Snapshot on significant events only (e.g., misconception detected, strategy switch threshold crossed).

---

## Issue #7: `learning_style_preferences` update is incomplete

**File**: `tools/cognition.py`

The PRD specifies that the tool should "update learning style preferences". Currently only `shaky_concepts` is tracked (concepts where the student was correct but slow/needed help). The `preferred_strategy` field in the model is always `None`.

**Dependency**: This becomes actionable after `construct_hint` (Worklist Task #3) is fully implemented. `construct_hint` should write its chosen strategy to the concept entry's `last_strategy` field. Then `update_student_cognition_map` can track which strategies led to correct answers and update `preferred_strategy` accordingly.

**Fix**: After Task #3, add logic:
1. Read `entry["last_strategy"]` for the current concept.
2. If `is_correct` and `last_strategy` is set, increment a per-strategy success counter.
3. Update `preferred_strategy` to the strategy with the highest success rate.

---

## Issue #8: Node doesn't persist full interaction episodes

**File**: `agents/companion/node.py`

The Logic Flow document (Phase 5) specifies: "存档交互：将完整交互记录（输入、输出、工具调用链、推理过程）写入 `interaction_episodes`". The current node only writes cognition snapshots (via the tool). The full interaction record (student input, companion response, tools called, reasoning chain) is not persisted.

**Fix**: In `socratic_companion_node`, after all tool calls, write an interaction episode:

```python
shared_memory.write("interaction_episodes", f"{student_id}:{session_id}:{timestamp}", {
    "type": "interaction_episode",
    "student_id": student_id,
    "input": current_input,
    "output": state["response_to_student"],
    "tools_called": state["tools_to_call"],
    "target_concept": target_concept,
    "timestamp": timestamp,
})
```

**Note**: This overlaps with Worklist Task #5 (node logic implementation), so it may be addressed there instead.

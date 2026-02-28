# Companion Task 8 Memory Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Task 8 by hardening Companion's shared-memory integration contract and ensuring first-turn cognition initialization is explicit and verifiable.

**Architecture:** Keep all changes inside Companion-owned files and shared memory contract declarations. Use test-first changes to lock expected memory schemas and state transitions, then apply minimal code updates to `memory/shared.py`, `tools/cognition.py`, and `agents/companion/node.py`.

**Tech Stack:** Python, pytest, in-memory shared memory proxy (`memory/shared.py`), Companion node/tools.

---

### Task 1: Lock Namespace Contract

**Files:**
- Modify: `tests/companion/test_memory_contract.py`
- Modify: `memory/shared.py`
- Test: `tests/companion/test_memory_contract.py`

**Step 1: Write the failing test**

Remove the xfail expectation and assert `cognition_snapshots` is declared in `NAMESPACES`.

**Step 2: Run test to verify it fails**

Run: `pytest tests/companion/test_memory_contract.py -k cognition_snapshots -v`
Expected: FAIL because `cognition_snapshots` is not declared in `memory/shared.py`.

**Step 3: Write minimal implementation**

Add `cognition_snapshots` to `NAMESPACES` in `memory/shared.py`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/companion/test_memory_contract.py -k cognition_snapshots -v`
Expected: PASS.

### Task 2: Enforce Concept Confidence-Uncertainty Sync

**Files:**
- Modify: `tests/companion/test_cognition.py`
- Modify: `tools/cognition.py`
- Test: `tests/companion/test_cognition.py`

**Step 1: Write the failing test**

Add tests asserting concept entries include `uncertainty` and maintain `confidence + uncertainty ~= 1.0` after updates.

**Step 2: Run test to verify it fails**

Run: `pytest tests/companion/test_cognition.py -k uncertainty -v`
Expected: FAIL because concept entries currently do not store `uncertainty`.

**Step 3: Write minimal implementation**

Update cognition model init/update paths so each concept entry stores synchronized `confidence` and `uncertainty`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/companion/test_cognition.py -k uncertainty -v`
Expected: PASS.

### Task 3: First-Turn Model Bootstrap in Node

**Files:**
- Modify: `tests/companion/test_node.py`
- Modify: `agents/companion/node.py`
- Test: `tests/companion/test_node.py`

**Step 1: Write the failing test**

Add an integration test that verifies first interaction initializes a default student model entry with `uncertainty=1.0` for target concept before/while processing the turn.

**Step 2: Run test to verify it fails**

Run: `pytest tests/companion/test_node.py -k "new_student and uncertainty" -v`
Expected: FAIL because node currently relies on downstream cognition update and has no explicit bootstrap.

**Step 3: Write minimal implementation**

Add node-level bootstrap helper to create default model and concept entry when student has no stored model.

**Step 4: Run test to verify it passes**

Run: `pytest tests/companion/test_node.py -k "new_student and uncertainty" -v`
Expected: PASS.

### Task 4: Full Companion Regression Slice

**Files:**
- Test: `tests/companion/test_memory_contract.py`
- Test: `tests/companion/test_cognition.py`
- Test: `tests/companion/test_node.py`

**Step 1: Run focused suite**

Run: `pytest tests/companion/test_memory_contract.py tests/companion/test_cognition.py tests/companion/test_node.py -v`
Expected: PASS with no new regressions.

**Step 2: Capture completion notes**

Document what was changed and any remaining risks for Task 9 (multi-turn script coverage).

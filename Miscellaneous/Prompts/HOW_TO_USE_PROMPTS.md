# How to Use the Phase Prompt Files

## Overview

This project includes **4 phase-specific prompt files** that break down each development phase into sequential, manageable chunks for GitHub Copilot:

- `phase_0_prompts.md` - Contracts, Synthetic Data & Manual Validation
- `phase_1_prompts.md` - Data Integration & Normalization
- `phase_2_prompts.md` - Analytics & Scoring Engine
- `phase_3_prompts.md` - Frontend MVP Interface
- `phase_4_prompts.md` - API, Deployment & End-to-End Testing

## Why This Approach?

**Problem**: Giving Copilot an entire phase in one go leads to:
- Hallucinated code (inventing non-existent functions/files)
- Inconsistent naming across modules
- Missed dependencies
- Incomplete implementations

**Solution**: Break each phase into **8-15 sequential prompts** that:
- Build on each other logically
- Reference previous work explicitly
- Include validation steps
- Force incremental progress

## How to Use (Step-by-Step)

### 1. Prerequisites

Before starting ANY phase:

```powershell
# Read the implementation plan
code IMPLEMENTATION_PLAN.md

# Read the startup details
code startup_details.md

# Check if previous phase is complete
code PHASE_LOG.md  # Should have entry for previous phase
```

### 2. Start Your Phase

Example: You're assigned **Phase 1**

```powershell
# Open the phase prompts file
code phase_1_prompts.md

# Read the entire file first (understand the flow)
# Note: There are 13 prompts for Phase 1
```

### 3. Execute Prompts Sequentially

**DO NOT skip or reorder prompts.** They are designed to build on each other.

#### Prompt 1: Read Context
Copy the text from **Prompt 1** section in `phase_1_prompts.md`:

```
I am implementing Phase 1 of the StartSmart MVP project (Data Integration).

First, please read PHASE_LOG.md to understand what Phase 0 delivered.

Then create the following directory structure under backend/:
...
```

Paste into **GitHub Copilot Chat** and wait for response.

**Copilot will**:
- Read PHASE_LOG.md (if available in context)
- Create the directory structure
- Generate __init__.py files

**You should**:
- Review the generated structure
- Verify files created correctly
- Run any suggested commands

#### Prompt 2: Next Step
Once Prompt 1 is complete, move to **Prompt 2**:

```
Create the database connection and ORM setup.

Please create `backend/src/database/connection.py`:
...
```

**Copilot will**:
- Generate the connection.py file
- Use SQLAlchemy 2.0 syntax
- Include error handling

**You should**:
- Review the code
- Check imports match contracts
- Test the connection (run suggested code)

#### Continue Through All Prompts

Repeat this process for **all 13 prompts** in Phase 1.

### 4. After Each Prompt

**Validation Checklist**:
- [ ] Code generated without errors
- [ ] Files created in correct locations
- [ ] Imports reference existing modules (not hallucinated)
- [ ] Code matches contracts (if applicable)
- [ ] Tests pass (if test prompt)

**If something is wrong**:
- Don't move to next prompt
- Ask Copilot to fix (be specific about the error)
- Re-run tests
- Document issue in notes

### 5. Phase Completion

The **final prompt** in each phase file is always: **"Update PHASE_LOG.md"**

Example from Phase 1:
```
Phase 1 is complete. Update PHASE_LOG.md with the Phase 1 handoff entry.

Append to PHASE_LOG.md following the exact format from IMPLEMENTATION_PLAN.md Phase 1 "Handoff to Phase 2" section.
...
```

**This is CRITICAL**:
- Copilot will generate the PHASE_LOG entry
- Review it carefully
- Fill in actual values (line counts, test results, etc.)
- This becomes the handoff to the next developer

### 6. Checklist Before Moving to Next Phase

Each phase file ends with a **completion checklist**. Example:

```markdown
## Phase 1 Completion Checklist

Before moving to Phase 2, verify:

- [ ] All files created under backend/src/
- [ ] GooglePlacesAdapter implements BaseAdapter interface
- [ ] businesses table populated (≥50 rows)
- [ ] PHASE_LOG.md updated with comprehensive handoff
...
```

**Go through EVERY item**. If any fail, FIX before proceeding.

## Tips for Success

### Tip 1: Read, Don't Just Copy-Paste

Before pasting a prompt:
1. Read it fully
2. Understand what it's asking for
3. Check if you have prerequisites (files, data, etc.)
4. Then paste and execute

### Tip 2: Keep PHASE_LOG.md Open

Always have PHASE_LOG.md visible:
- It shows what's already done
- Copilot references it frequently
- You'll need to update it

### Tip 3: Test Incrementally

Don't wait until the end to test. After prompts that generate code:

```powershell
# Run tests immediately
pytest backend/tests/adapters/test_google_places_adapter.py -v

# Or run the code
python backend/src/adapters/google_places_adapter.py
```

### Tip 4: Document Issues in Real-Time

If you encounter problems:
- Add to a notes file immediately
- Include prompt number (e.g., "Phase 1, Prompt 6: Import error")
- Document solution
- Update Known Issues in PHASE_LOG when done

### Tip 5: Use Version Control

Commit after each major prompt (every 2-3 prompts):

```powershell
git add .
git commit -m "Phase 1: Implemented GooglePlacesAdapter (Prompt 6-7)"
git push origin phase-1/data-integration
```

This makes rollback easy if something breaks.

## Common Pitfalls

### ❌ Pitfall 1: Skipping Prompts
**Why it fails**: Later prompts assume earlier work exists.

**Example**: Skipping Prompt 2 (database connection) causes Prompt 5 (geospatial service) to fail because it can't import get_session().

**Solution**: Follow order strictly.

### ❌ Pitfall 2: Not Reading PHASE_LOG
**Why it fails**: You don't know what previous phase created.

**Example**: Phase 2 assumes BusinessModel exists from Phase 1. If you don't read PHASE_LOG, you might create a new Business class and cause conflicts.

**Solution**: Always read PHASE_LOG first (it's in Prompt 1 of every phase).

### ❌ Pitfall 3: Ignoring Test Failures
**Why it fails**: Bugs compound. A failing test in Prompt 5 breaks Prompt 10.

**Solution**: Fix tests immediately. Don't move forward with failing tests.

### ❌ Pitfall 4: Incomplete PHASE_LOG Updates
**Why it fails**: Next developer doesn't know what you did.

**Example**: You forget to document the grid_id format. Next developer uses wrong format, database queries fail.

**Solution**: Use the comprehensive template. Fill in ALL sections.

### ❌ Pitfall 5: Pasting Multiple Prompts at Once
**Why it fails**: Copilot gets confused and generates incomplete code.

**Solution**: ONE prompt at a time. Wait for completion. Validate. Then next prompt.

## Example Workflow (Phase 1)

Here's what a successful Phase 1 implementation looks like:

### Day 1 (Prompts 1-5)
```
9:00 AM  - Read IMPLEMENTATION_PLAN.md and PHASE_LOG.md
9:30 AM  - Open phase_1_prompts.md
10:00 AM - Execute Prompt 1 (directory structure) ✅
10:15 AM - Execute Prompt 2 (database connection) ✅
10:45 AM - Test database connection - works ✅
11:00 AM - Execute Prompt 3 (ORM models) ✅
11:30 AM - Verify models match schema ✅
12:00 PM - Lunch
1:00 PM  - Execute Prompt 4 (logger utility) ✅
1:30 PM  - Execute Prompt 5 (geospatial service) ✅
2:00 PM  - Test geospatial with sample coordinates ✅
2:30 PM  - Commit: "Phase 1: Database layer and geospatial service"
```

### Day 2 (Prompts 6-9)
```
9:00 AM  - Review yesterday's work
9:30 AM  - Execute Prompt 6 (Google Places Adapter - Part 1) ✅
10:30 AM - Execute Prompt 7 (Google Places Adapter - Part 2) ✅
11:00 AM - Test with mock Google API - works ✅
11:30 AM - Execute Prompt 8 (Simulated Social Adapter) ✅
12:00 PM - Lunch
1:00 PM  - Execute Prompt 9 (Business Fetching CLI) ✅
1:30 PM  - Run CLI with real Google Places API key ✅
2:00 PM  - Verify 73 businesses in database ✅
2:30 PM  - Commit: "Phase 1: Data adapters and CLI tool"
```

### Day 3 (Prompts 10-13)
```
9:00 AM  - Execute Prompt 10 (Google Places tests) ✅
10:00 AM - All tests pass - 87% coverage ✅
10:30 AM - Execute Prompt 11 (Geospatial tests) ✅
11:00 AM - All tests pass - 95% coverage ✅
11:30 AM - Execute Prompt 12 (Integration test) ✅
12:00 PM - Integration test passes ✅
12:30 PM - Lunch
1:30 PM  - Execute Prompt 13 (Update PHASE_LOG.md) ✅
2:00 PM  - Review PHASE_LOG entry - comprehensive ✅
2:30 PM  - Run full test suite - all pass ✅
3:00 PM  - Complete Phase 1 checklist - all items checked ✅
3:30 PM  - Commit: "Phase 1: Complete with tests and documentation"
4:00 PM  - Create PR for review
```

**Result**: Phase 1 complete in 3 days with high quality.

## Handoff Between Developers

When you complete your phase and the next developer starts:

### You (Outgoing Developer)
1. Ensure PHASE_LOG.md is comprehensive
2. Push all code to repo
3. Create a handoff meeting (15 mins)
4. Walk through:
   - What you built
   - Any tricky parts
   - Known issues
   - How to run/test

### Next Developer (Incoming)
1. Read PHASE_LOG.md thoroughly
2. Run all tests from previous phase
3. Verify database state matches documentation
4. Ask questions (use handoff meeting)
5. Only then start your phase prompts

## Emergency: What If Copilot Hallucinates?

Sometimes Copilot invents code that doesn't exist. Here's how to handle it:

### Step 1: Identify the Issue
Copilot says: `from src.utils.helpers import calculate_distance`

But `helpers.py` doesn't exist.

### Step 2: Check PHASE_LOG
Search PHASE_LOG for "helpers" or "calculate_distance".

If not found → Hallucination confirmed.

### Step 3: Fix
Ask Copilot:
```
The function calculate_distance does not exist. Please implement it in src/utils/helpers.py
OR
Please use an alternative approach that doesn't require calculate_distance
```

### Step 4: Document
Add to notes:
```
Phase X, Prompt Y: Copilot hallucinated calculate_distance. Fixed by implementing in helpers.py.
```

### Step 5: Continue
Once fixed, proceed with next prompt.

## Summary

**Success Formula**:
1. ✅ Read IMPLEMENTATION_PLAN.md first
2. ✅ Read PHASE_LOG.md before each phase
3. ✅ Execute prompts sequentially (one at a time)
4. ✅ Test after each major prompt
5. ✅ Commit frequently
6. ✅ Update PHASE_LOG comprehensively
7. ✅ Complete checklist before moving on

**Avoid**:
1. ❌ Skipping prompts
2. ❌ Pasting multiple prompts at once
3. ❌ Ignoring test failures
4. ❌ Incomplete PHASE_LOG updates
5. ❌ Not reading previous phase handoff

Follow this guide, and you'll deliver a high-quality MVP that impresses investors and instructors.

**Questions?** Re-read this guide or check IMPLEMENTATION_PLAN.md Section 5 (PHASE_LOG).

Good luck! 🚀

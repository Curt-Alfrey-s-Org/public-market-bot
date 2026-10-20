# Copilot Sentinel Workflow - Visual Guide

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pull Request Created                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   Copilot Sentinel Workflow   │
         │        Triggered              │
         └───────────────┬───────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │  Is this a Copilot PR?        │
         │  (Check author, branch, title)│
         └───────────┬───────────────────┘
                     │
           ┌─────────┴──────────┐
           │                    │
          NO                   YES
           │                    │
           ▼                    ▼
    ┌──────────┐      ┌──────────────────┐
    │  PASS    │      │  Check Completion│
    │ (Green)  │      │    Signals       │
    └──────────┘      └─────────┬────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
         ┌─────────────────┐    ┌──────────────────┐
         │ Has Completion  │    │ Check Commit     │
         │ Label/Marker?   │    │ Timing & WIP     │
         └────────┬────────┘    └────────┬─────────┘
                  │                      │
         ┌────────┴──────┐      ┌────────┴──────┐
         │               │      │               │
        YES             NO     YES              NO
         │               │      │               │
         ▼               │      ▼               ▼
    ┌──────────┐        │  ┌──────────┐   ┌──────────┐
    │  PASS    │◄───────┘  │  FAIL    │   │  PASS    │
    │ (Green)  │           │  (Red)   │   │ (Green)  │
    └──────────┘           └──────────┘   └──────────┘
         │                      │               │
         └──────────┬───────────┴───────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Other Status Checks │
         │  (Tests, Lint, etc.) │
         └──────────┬───────────┘
                    │
           ┌────────┴─────────┐
           │                  │
      ALL PASS           ANY FAIL
           │                  │
           ▼                  ▼
    ┌─────────────┐    ┌─────────────┐
    │ Merge Button│    │ Merge Button│
    │   GREEN ✅  │    │  BLOCKED ❌ │
    └─────────────┘    └─────────────┘
```

## Detection Logic Flow

### For Copilot PRs

```
┌─────────────────────────────────────┐
│  Copilot PR Detected                │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Check 1: Has Completion Label?       │
│ - copilot-completed                  │
│ - ready-to-merge                     │
└──────────────┬───────────────────────┘
               │
        YES────┤────NO
               │         │
               ▼         ▼
           [PASS]   ┌─────────────────────────┐
                    │ Check 2: Commit Message? │
                    │ - "complete"              │
                    │ - "finished"              │
                    │ - "done"                  │
                    │ - "ready for review"      │
                    └──────────┬────────────────┘
                               │
                        YES────┤────NO
                               │         │
                               ▼         ▼
                           [PASS]   ┌─────────────────────┐
                                    │ Check 3: Commit Age? │
                                    │ > 5 minutes?         │
                                    └──────────┬───────────┘
                                               │
                                        YES────┤────NO
                                               │         │
                                               ▼         ▼
                                           [PASS]   ┌─────────────────┐
                                                    │ Check 4: WIP?    │
                                                    │ - "WIP"          │
                                                    │ - "initial plan" │
                                                    │ - "progress:"    │
                                                    └──────┬───────────┘
                                                           │
                                                    YES────┤────NO
                                                           │         │
                                                           ▼         ▼
                                                       [FAIL]   ┌───────────────┐
                                                                │ Check 5: Age? │
                                                                │ < 2 minutes?  │
                                                                └──────┬────────┘
                                                                       │
                                                                YES────┤────NO
                                                                       │         │
                                                                       ▼         ▼
                                                                   [FAIL]    [PASS]
```

## Status Check Examples

### Example 1: Copilot Still Working

```
PR #123: copilot/fix-bug-in-module

Checks:
❌ Copilot Work Status - Copilot is still working
   ⏳ Last commit: "Initial plan" (1 minute ago)
   
🔒 Merge button: BLOCKED (gray)
```

### Example 2: Copilot Work Complete (Label)

```
PR #123: copilot/fix-bug-in-module

Labels: copilot-completed

Checks:
✅ Copilot Work Status - Work complete
✅ test (3.10) - All tests passed
✅ test (3.11) - All tests passed
✅ test (3.12) - All tests passed
✅ lint - Code quality checks passed

✅ Merge button: ENABLED (green)
```

### Example 3: Copilot Work Complete (Timing)

```
PR #123: copilot/fix-bug-in-module

Checks:
✅ Copilot Work Status - Work complete
   ⏰ Last commit: "Add feature" (6 minutes ago)
✅ test (3.10) - All tests passed
✅ test (3.11) - All tests passed  
✅ test (3.12) - All tests passed
✅ lint - Code quality checks passed

✅ Merge button: ENABLED (green)
```

### Example 4: Regular PR (Non-Copilot)

```
PR #124: feature/add-new-feature

Checks:
✅ Copilot Work Status - Not a Copilot PR
✅ test (3.10) - All tests passed
✅ test (3.11) - All tests passed
✅ test (3.12) - All tests passed
✅ lint - Code quality checks passed

✅ Merge button: ENABLED (green)
```

## User Actions

### For Copilot Users

#### When Copilot Finishes Work

**Option A: Add Label** (Fastest)
```
1. Click "Labels" in PR sidebar
2. Select "copilot-completed" or "ready-to-merge"
3. Wait for checks to re-run (automatic)
4. ✅ Merge button turns green
```

**Option B: Update Commit Message**
```
1. git commit --allow-empty -m "Implementation complete and ready"
2. git push
3. Wait for checks to run
4. ✅ Merge button turns green
```

**Option C: Wait** (Automatic)
```
1. Stop making commits
2. Wait 5 minutes
3. Check automatically passes
4. ✅ Merge button turns green
```

### For PR Reviewers

```
1. View PR status checks section
2. Look for "Copilot Work Status" check
   - ✅ Green = Ready to review
   - ❌ Red = Still working, wait
3. If green, proceed with review
4. After approval, PR can be merged
```

## Timeline Example

```
Time    Event                          Status Check
─────   ────────────────────────────   ─────────────────
0:00    Copilot opens PR               ❌ Still working
        Commit: "Initial plan"
        
0:02    Copilot makes progress         ❌ Still working
        Commit: "Add implementation"
        
0:05    Copilot makes more changes     ❌ Still working
        Commit: "Fix tests"
        
0:08    Copilot finishes               ✅ Work complete
        Commit: "Final implementation    (auto-detected
                complete"                after 5 min)
        
0:09    All tests run and pass         ✅ All checks pass
        
0:10    PR is merged                   ✅ Merged
```

## Key Insights

### What BLOCKS Merging

1. ❌ Copilot Sentinel fails (detects ongoing work)
2. ❌ Tests fail
3. ❌ Linting fails
4. ❌ Security scans fail (optional)
5. ❌ Missing required review approval

### What ALLOWS Merging

1. ✅ All status checks pass (green)
2. ✅ At least 1 approved review
3. ✅ Branch is up to date
4. ✅ All conversations resolved

### False Positive Prevention

The Copilot Sentinel is designed to **err on the side of caution**:

- If uncertain → ALLOW merge (after timeout)
- Recent activity → BLOCK merge
- Clear WIP markers → BLOCK merge
- Clear completion signals → ALLOW merge

This prevents:
- ❌ Premature merges (blocks when unsure)
- ✅ Stuck PRs (auto-passes after timeout)

## Benefits Summary

| Before | After |
|--------|-------|
| ❌ No indication Copilot is working | ✅ Clear status check shows work status |
| ❌ Merge button always green | ✅ Merge blocked while working |
| ❌ Manual monitoring required | ✅ Automatic detection |
| ❌ Risk of premature merge | ✅ Prevents premature merges |
| ❌ No quality gates | ✅ Tests must pass to merge |

## Next Steps

For repository administrators:
1. Configure branch protection rules
2. Add required status checks
3. Test with a Copilot PR

## Auto-Label + Gate Integration

- Copilot PRs (branches starting with `copilot/`) are automatically labeled `copilot-completed` when all checks pass.
- The label gate re-evaluates on the `labeled` event and allows merging once the label is present.
- If automation hasn’t labeled the PR yet, add the label via PR sidebar (Labels → `copilot-completed`) to pass the gate.


See [BRANCH_PROTECTION_GUIDE.md](BRANCH_PROTECTION_GUIDE.md) for detailed setup instructions.

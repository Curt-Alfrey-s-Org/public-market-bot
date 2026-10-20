# Branch Protection Configuration Guide

## Overview

This guide explains how to configure GitHub branch protection rules to prevent premature PR merges, especially when GitHub Copilot is still working on a pull request.

## Problem Statement

Previously, PRs could be merged even when GitHub Copilot was still actively working on them, because:

1. The merge button appeared green (enabled) with no clear indication of ongoing work
2. Status checks had `continue-on-error: true`, so they never blocked merges
3. There was no explicit status check for Copilot completion

## Solution

The repository now includes:

1. **Copilot Sentinel Workflow** (`.github/workflows/copilot-sentinel.yml`): A required status check that detects when Copilot is working
2. **Updated Test Workflow**: Tests now properly fail if they don't pass
3. **Updated Lint Workflow**: Critical linting errors now block merges
4. **Branch Protection Requirements**: Documentation for configuring required status checks

## Configuring Branch Protection (Repository Administrators)

To enable these protections, repository administrators should follow these steps:

### Step 1: Navigate to Branch Protection Settings

1. Go to your repository on GitHub
2. Click **Settings** (top navigation)
3. Click **Branches** (left sidebar)
4. Find the branch protection rule for `main` (or create one if it doesn't exist)
5. Click **Edit** (or **Add branch protection rule**)

### Step 2: Configure Required Status Checks

Enable the following settings:

#### Basic Protection
- ✅ **Require a pull request before merging**
  - Require approvals: **1** (at least one human review)
  - Dismiss stale pull request approvals when new commits are pushed

#### Required Status Checks
- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**

Add the following status checks as required:

1. **`Copilot Work Status`** - Ensures Copilot has finished working
2. **`test (3.10)`** - Python 3.10 tests must pass
3. **`test (3.11)`** - Python 3.11 tests must pass
4. **`test (3.12)`** - Python 3.12 tests must pass
5. **`lint`** - Code quality checks must pass
6. **`security`** - Security scans must pass (optional but recommended)
7. **`CodeQL Analysis`** - Code security analysis (optional but recommended)

#### Additional Recommended Settings
- ✅ **Require conversation resolution before merging** - All review comments must be resolved
- ✅ **Require linear history** - Prevents merge commits (optional)
- ✅ **Do not allow bypassing the above settings** - Applies rules to administrators too

### Step 3: Save Changes

Click **Create** or **Save changes** at the bottom of the page.

## How the Copilot Sentinel Works

The Copilot Sentinel workflow (`.github/workflows/copilot-sentinel.yml`) automatically detects if Copilot is still working by checking:

### Detection Criteria

1. **PR Author**: Is the PR from a Copilot bot or branch?
2. **Labels**: Does the PR have `copilot-completed` or `ready-to-merge` labels?
3. **Commit Messages**: Does the last commit indicate completion (contains "complete", "finished", "done", etc.)?
4. **Timing**: Was the last commit more than 5 minutes ago?
5. **WIP Markers**: Does the PR contain work-in-progress indicators ("WIP", "initial plan", "progress:", etc.)?

### Status Results

- ✅ **Pass**: PR is ready to merge (Copilot has finished or not a Copilot PR)
- ❌ **Fail**: Copilot is still working - merge button will be blocked

## For Copilot Users: Marking Work as Complete

When GitHub Copilot finishes working on a PR, you can mark it as complete in several ways:

### Option 1: Add a Label (Recommended)
Add one of these labels to the PR:
- `copilot-completed`
- `ready-to-merge`

### Option 2: Update Commit Message
Ensure the final commit message includes one of these keywords:
- "complete"
- "finished"
- "done"
- "ready for review"
- "ready to merge"

### Option 3: Wait for Automatic Detection
The sentinel will automatically pass the check after:
- 5 minutes of no new commits
- No work-in-progress markers detected

### Option 4: Manual Review
Request a human review, and the reviewer can add the appropriate label.

## Troubleshooting

### Merge Button Still Green Despite Copilot Working

**Cause**: Branch protection rules are not configured or status checks are not required.

**Solution**: Follow the configuration steps above to add required status checks.

### Copilot Sentinel Fails Incorrectly

**Cause**: PR appears to be from Copilot but work is actually complete.

**Solution**: 
1. Add the `copilot-completed` label to the PR
2. OR wait 5 minutes after the last commit
3. OR update the last commit message to include "complete" or "finished"

### Status Check Doesn't Appear

**Cause**: The workflow may not have been triggered.

**Solution**:
1. Ensure the workflow file exists: `.github/workflows/copilot-sentinel.yml`
2. Make a new commit or close/reopen the PR to trigger the workflow
3. Check the **Actions** tab to see if the workflow ran

### Tests Failing After Update

**Cause**: Tests now properly fail instead of continuing with errors.

**Solution**:
1. Review the test failure logs in the **Actions** tab
2. Fix the failing tests
3. Commit the fixes
4. The status check will automatically re-run

## Benefits

With these protections in place:

1. ✅ **No Premature Merges**: PRs cannot be merged while Copilot is still working
2. ✅ **Clear Status**: Visual indication in the PR checks section shows Copilot work status
3. ✅ **Quality Gates**: Tests and linting must pass before merge
4. ✅ **Human Oversight**: At least one human review is required
5. ✅ **Automatic Detection**: No manual intervention needed in most cases

## Related Files

- `.github/workflows/copilot-sentinel.yml` - Copilot status check workflow
- `.github/workflows/copilot-label-gate.yml` - Requires `copilot-completed` label on Copilot PRs
- `.github/workflows/copilot-auto-label.yml` - Automatically adds `copilot-completed` when all checks pass
- `.github/workflows/tests.yml` - Test workflow (updated to fail properly)
- `.github/workflows/lint.yml` - Linting workflow (updated to fail properly)
- `.github/workflows/security.yml` - Security scanning workflow

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/
- [GitHub Status Checks Documentation](https://docs.github.com/
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)

## Questions or Issues?

If you encounter issues with the branch protection setup or Copilot Sentinel workflow:

1. Check the **Actions** tab in the repository to see workflow run details
2. Review this guide to ensure all steps were followed correctly
3. Create an issue in the repository with details about the problem
4. Tag the issue with `branch-protection` or `copilot` for faster triage

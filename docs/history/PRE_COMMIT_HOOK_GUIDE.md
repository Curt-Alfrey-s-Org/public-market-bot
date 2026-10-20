# Pre-Commit Hook Installation Guide

This guide explains how to install and use the pre-commit hook to maintain code quality.

## What It Does

The pre-commit hook automatically checks your code before each commit:

- ✅ **Syntax errors** - Catches Python syntax errors
- ✅ **Undefined names** - Finds undefined variables and imports
- ⚠️ **Unused imports/variables** - Warns about unused code (doesn't block commit)
- ⚠️ **Code formatting** - Checks black formatting (doesn't block commit)
- ⚠️ **Import sorting** - Checks isort compliance (doesn't block commit)
- ⚠️ **Debugging statements** - Warns about print/pdb/breakpoint
- ⚠️ **TODO/FIXME** - Suggests linking to issue numbers

## Installation

### Automatic Installation (Recommended)

```bash
# From repository root
./pre-commit-hook.sh install

# Or manually:
cp pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Manual Installation

1. Copy the hook:
   ```bash
   cp pre-commit-hook.sh .git/hooks/pre-commit
   ```

2. Make it executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. Verify installation:
   ```bash
   ls -la .git/hooks/pre-commit
   ```

## Usage

Once installed, the hook runs automatically on `git commit`:

```bash
# Make changes to Python files
git add main.py

# Commit - hook runs automatically
git commit -m "Update trading logic"

# Output example:
🔍 Running pre-commit checks...
Checking Python files:
main.py

📋 Checking for syntax errors...
✅ No syntax errors

📋 Checking for unused imports...
⚠️  Unused imports or variables found
main.py:15:1: F401 'os' imported but unused

📋 Checking code formatting...
✅ Code formatting is correct

✅ All critical checks passed!
```

## Handling Warnings vs Errors

### Errors (Block Commit)
- ❌ Syntax errors (E9)
- ❌ Undefined names (F63, F7, F82)

**Action Required:** Fix these errors before committing.

### Warnings (Don't Block Commit)
- ⚠️ Unused imports (F401)
- ⚠️ Unused variables (F841)
- ⚠️ Formatting issues
- ⚠️ Import sorting
- ⚠️ Debugging statements
- ⚠️ TODO without issue number

**Action Recommended:** Fix these to avoid automated security bot commits.

## Fixing Common Issues

### Unused Imports
```bash
# Auto-fix with autoflake
pip install autoflake
autoflake --remove-all-unused-imports --in-place main.py
```

### Code Formatting
```bash
# Auto-fix with black
black .
```

### Import Sorting
```bash
# Auto-fix with isort
isort .
```

### All at Once
```bash
# Fix everything in one go
autoflake --remove-all-unused-imports --remove-unused-variables --in-place *.py
black .
isort .
```

## Bypassing the Hook

**Not recommended**, but sometimes necessary:

```bash
# Skip pre-commit checks
git commit --no-verify -m "Emergency fix"
```

**When to bypass:**
- Emergency hotfixes
- Work-in-progress commits to feature branches
- Intentional code patterns that trigger false positives

**Do NOT bypass for:**
- Main branch commits
- Pull request commits
- Production releases

## Troubleshooting

### Hook doesn't run
```bash
# Check if hook is installed
ls -la .git/hooks/pre-commit

# Check if executable
chmod +x .git/hooks/pre-commit

# Test manually
.git/hooks/pre-commit
```

### "flake8 not found"
```bash
# Install in virtual environment
source venv/bin/activate
pip install flake8 black isort autoflake
```

### "Not in a virtual environment" warning
```bash
# Activate virtual environment before committing
source venv/bin/activate
git commit -m "Your message"
```

### Hook runs but no Python files
The hook only checks Python files that are staged for commit:
```bash
# Make sure to git add your changes
git add *.py
git commit -m "Your message"
```

## Configuration

### Customizing Checks

Edit `.git/hooks/pre-commit` to customize:

```bash
# Change which flake8 errors to check
flake8 --select=E9,F63,F7,F82,F401,F841

# Add more strict checks
flake8 --max-line-length=127 --max-complexity=10

# Skip specific checks
flake8 --ignore=E203,W503
```

### Per-Project Configuration

Create `.flake8` in repository root:

```ini
[flake8]
max-line-length = 127
exclude = venv,node_modules,.git,__pycache__
ignore = E203,W503
select = E9,F63,F7,F82,F401,F841
```

## CI/CD Integration

The same checks run in CI/CD workflows. To match CI behavior locally:

```bash
# Run full CI checks locally
./.github/workflows/lint.yml  # (if you have act installed)

# Or run checks manually
flake8 . --count --select=E9,F63,F7,F82 --statistics --exclude=venv,node_modules
black --check .
isort --check-only .
```

## Benefits

✅ **Catch errors early** - Before they reach CI/CD  
✅ **Consistent code style** - Across all contributors  
✅ **Fewer automated fixes** - Reduce security bot commits  
✅ **Better code quality** - Cleaner, more maintainable code  
✅ **Faster reviews** - Less time spent on style issues  

## Maintenance

### Updating the Hook

When the hook script is updated in the repository:

```bash
# Re-install the updated version
cp pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Removing the Hook

```bash
# Remove the hook
rm .git/hooks/pre-commit
```

## Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - Code style guide
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md#2-code-quality-alerts) - Code quality issue tracking

---

**Questions?** Open an issue with the `question` label.

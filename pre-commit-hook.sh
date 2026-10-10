#!/bin/bash
#
# Pre-commit hook to check code quality
# Install: cp pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#
# This hook checks for:
# - Python syntax errors
# - Unused variables and imports
# - Code formatting issues
# - Import sorting
#

set -e

echo "🔍 Running pre-commit checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Not in a virtual environment${NC}"
    echo "Consider activating venv: source venv/bin/activate"
fi

# Get list of Python files to check
PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$PYTHON_FILES" ]; then
    echo -e "${GREEN}✅ No Python files to check${NC}"
    exit 0
fi

echo "Checking Python files:"
echo "$PYTHON_FILES"
echo ""

# Track if any checks fail
CHECKS_FAILED=0

# 1. Check for Python syntax errors and undefined names
echo "📋 Checking for syntax errors and undefined names..."
if ! flake8 $PYTHON_FILES --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,node_modules,.git; then
    echo -e "${RED}❌ Syntax errors or undefined names found${NC}"
    CHECKS_FAILED=1
else
    echo -e "${GREEN}✅ No syntax errors${NC}"
fi
echo ""

# 2. Check for unused variables and imports
echo "📋 Checking for unused variables and imports..."
if ! flake8 $PYTHON_FILES --count --select=F401,F841 --statistics --exclude=venv,node_modules,.git; then
    echo -e "${YELLOW}⚠️  Unused imports or variables found${NC}"
    echo "These will be flagged by automated checks. Consider fixing them."
    # Don't fail the commit, just warn
else
    echo -e "${GREEN}✅ No unused imports or variables${NC}"
fi
echo ""

# 3. Check code formatting with black
echo "📋 Checking code formatting..."
if command -v black &> /dev/null; then
    if ! black --check --quiet $PYTHON_FILES 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Code formatting issues found${NC}"
        echo "Run 'black .' to auto-fix formatting"
        # Don't fail the commit, just warn
    else
        echo -e "${GREEN}✅ Code formatting is correct${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  black not installed, skipping format check${NC}"
fi
echo ""

# 4. Check import sorting
echo "📋 Checking import sorting..."
if command -v isort &> /dev/null; then
    if ! isort --check-only --quiet $PYTHON_FILES 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Import sorting issues found${NC}"
        echo "Run 'isort .' to auto-fix imports"
        # Don't fail the commit, just warn
    else
        echo -e "${GREEN}✅ Imports are sorted correctly${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  isort not installed, skipping import check${NC}"
fi
echo ""

# 5. Check for common issues
echo "📋 Checking for common issues..."
COMMON_ISSUES=0

# Check for debugging statements
if git diff --cached | grep -E "print\(|pdb\.set_trace\(\)|breakpoint\(\)" > /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Found debugging statements (print/pdb/breakpoint)${NC}"
    COMMON_ISSUES=1
fi

# Check for TODO/FIXME without issue numbers
if git diff --cached | grep -E "TODO:|FIXME:" | grep -v "#[0-9]" > /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Found TODO/FIXME without issue number${NC}"
    echo "Consider linking to an issue: TODO(#123): description"
    COMMON_ISSUES=1
fi

if [ $COMMON_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ No common issues found${NC}"
fi
echo ""

# Summary
if [ $CHECKS_FAILED -eq 1 ]; then
    echo -e "${RED}❌ Pre-commit checks FAILED${NC}"
    echo "Please fix the errors above before committing."
    echo ""
    echo "To bypass this hook (not recommended):"
    echo "  git commit --no-verify"
    exit 1
else
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo ""
    exit 0
fi

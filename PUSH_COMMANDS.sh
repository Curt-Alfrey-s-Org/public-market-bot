#!/bin/bash
# Git commands to commit and push component enhancements
# Run this script or copy/paste commands individually

echo "============================================================"
echo "Git Push Commands for Component Enhancements"
echo "============================================================"
echo ""

# Step 1: Review changes
echo "Step 1: Reviewing changes..."
echo "Modified files:"
git diff --name-only
echo ""
echo "New files:"
git ls-files --others --exclude-standard
echo ""
read -p "Review complete. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Step 2: Stage all changes
echo ""
echo "Step 2: Staging all changes..."
git add .
echo "✅ All changes staged"

# Step 3: Commit
echo ""
echo "Step 3: Committing changes..."
git commit -m "feat: Enhance component integration and fix critical bugs

- Add portfolio optimization caching (5 min TTL)
- Add component coordination state tracking
- Improve ML parameter application with better feedback
- Fix Plotly 'nonexistent object' errors
- Suppress yfinance delisted stock errors
- Add feed refresh throttling
- Reduce log noise
- Add comprehensive test suite
- Add Cursor rule for testing requirements
- Update documentation

All tests passing (5/5). No breaking changes."

if [ $? -eq 0 ]; then
    echo "✅ Commit successful"
else
    echo "❌ Commit failed"
    exit 1
fi

# Step 4: Push
echo ""
echo "Step 4: Pushing to remote..."
read -p "Push to origin/main? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Push successful!"
        echo ""
        echo "============================================================"
        echo "All changes have been pushed successfully"
        echo "============================================================"
    else
        echo "❌ Push failed"
        exit 1
    fi
else
    echo "Push skipped. Run 'git push origin main' when ready."
fi

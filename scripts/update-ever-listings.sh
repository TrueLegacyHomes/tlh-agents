#!/bin/bash
set -e
cd /Users/admin/.openclaw/workspace/tlh-agents
python3 scripts/update-ever-listings.py
gh auth switch --user brett-tlh 2>/dev/null || true
git add -A
git diff --cached --quiet && echo "No changes to commit" && exit 0
git commit -m "Auto-update: Ever San Diego listings $(date +%Y-%m-%d)"
git push origin main
echo "✅ Pushed to main"

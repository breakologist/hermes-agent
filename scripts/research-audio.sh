#!/usr/bin/env bash
# research-audio.sh — quick audio synthesis research queries
# Usage: ~/.hermes/scripts/research-audio.sh [query...]
# Falls back through ddgs → w3m+htmlq → curl+python

set -e

QUERY="${1:-Furnace tracker module format}"

echo "=== Researching: $QUERY ==="

# Try ddgs first
if command -v ddgs &>/dev/null; then
    echo "Method: ddgs CLI"
    ddgs text -k "$QUERY" -m 5 -o json | python3 -m json.tool 2>/dev/null && exit 0
fi

# Fallback: w3m dump + grep
if command -v w3m &>/dev/null; then
    echo "Method: w3m -dump"
    w3m -dump "https://duckduckgo.com/html/?q=${QUERY}" | head -40
    exit 0
fi

# Last resort: curl
echo "Method: curl raw"
curl -s -L -A "Mozilla/5.0" "https://duckduckgo.com/html/?q=${QUERY}" | head -50

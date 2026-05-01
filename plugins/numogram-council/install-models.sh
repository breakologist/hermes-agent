#!/bin/bash
# =====================================================================
# Numogram Council — Model Installation
# =====================================================================
#
# Pulls the three council models into ollama.
# Each model is loaded serially (one at a time in 12GB VRAM).
#
# Run: bash ~/.hermes/plugins/numogram-council/install-models.sh
#
# Models:
#   Slot 1: qwen2.5-coder:14b (reasoning/code, ~9GB)
#   Slot 2: mythomax-l2-13b (creative/mythic, ~8GB)
#   Slot 3: gemma3:12b-it (Google, balanced, ~7GB)
#   Judge fallback: hermes-14b (already installed)
#
# Note: Some models may not be in ollama registry.
# Check https://ollama.com/library for available models.
# =====================================================================

set -e

echo "=== Numogram Council Model Installation ==="
echo ""

# ---- Slot 1: Qwen2.5-Coder-14B ----
echo "[1/3] Slot 1: qwen2.5-coder:14b"
if ollama list 2>/dev/null | grep -q "qwen2.5-coder"; then
    echo "  ✓ Already installed"
else
    # Check if we have a local GGUF
    GGUF=$(find ~/.local/share/jan.ai.app -name "*qwen2.5-coder-14b*gguf" 2>/dev/null | head -1)
    if [ -n "$GGUF" ]; then
        echo "  Creating from local GGUF: $GGUF"
        SZ=$(du -h "$GGUF" | cut -f1)
        echo "  Size: $SZ"
        if [ "$SZ" \< "8.0G" ]; then
            cat > /tmp/modelfile_qcoder << EOF
FROM $GGUF
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
SYSTEM "You are a precise, analytical model. Think carefully and be direct."
EOF
            ollama create qwen2.5-coder:14b -f /tmp/modelfile_qcoder
            echo "  ✓ Created"
        else
            echo "  ⚠ GGUF too large ($SZ). Need smaller quant (Q3_K_M or Q4_K_M)."
            echo "  Trying ollama pull..."
            ollama pull qwen2.5-coder:14b 2>/dev/null || echo "  ⚠ Not in ollama registry. Install smaller GGUF."
        fi
    else
        echo "  Pulling from ollama..."
        ollama pull qwen2.5-coder:14b 2>/dev/null || echo "  ⚠ Not available. Use fallback: qwen2.5:7b-instruct"
    fi
fi

echo ""

# ---- Slot 2: MythoMax-L2-13B ----
echo "[2/3] Slot 2: mythomax-l2-13b"
if ollama list 2>/dev/null | grep -q "mythomax"; then
    echo "  ✓ Already installed"
else
    echo "  Pulling from ollama..."
    ollama pull mythomax-l2-13b 2>/dev/null || echo "  ⚠ Not in ollama registry. Use fallback: lelantos-7b"
fi

echo ""

# ---- Slot 3: Gemma3:12b-it ----
echo "[3/3] Slot 3: gemma3:12b-it"
if ollama list 2>/dev/null | grep -q "gemma3"; then
    echo "  ✓ Already installed"
else
    echo "  Pulling from ollama..."
    ollama pull gemma3:12b-it 2>/dev/null || echo "  ⚠ Not in ollama registry. Use fallback: qwen3.5-9b-heretic"
fi

echo ""

# ---- Summary ----
echo "=== Installed Models ==="
ollama list 2>/dev/null | grep -E "qwen|mytho|gemma|lelantos|hermes"
echo ""
echo "Council slots:"
echo "  Slot 1: qwen2.5-coder:14b (fallback: qwen2.5:7b-instruct)"
echo "  Slot 2: mythomax-l2-13b (fallback: lelantos-7b)"
echo "  Slot 3: gemma3:12b-it (fallback: qwen3.5-9b-heretic)"
echo "  Judge: mimo-v2-pro (fallback: hermes-14b)"
echo ""
echo "To use: council_decide(question='...', mode_override='creative')"

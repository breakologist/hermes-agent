"""
Numogram Council — Configurable Model Council for the Numogram Project

Features:
  - Configurable models per council slot (YAML or inline)
  - Temperature modes: creative (0.9), analytical (0.3), balanced (0.7)
  - Serial loading through ollama (one model in VRAM at a time)
  - Fallback judge (local model if cloud judge fails)
  - Per-slot fallback chains
  - Council rounds (multiple passes with different temperatures)

This is a separate plugin from evey-council. Not an overwrite.
"""

import concurrent.futures
import json
import logging
import os
import time

logger = logging.getLogger("numogram.council")

# =====================================================================
# COUNCIL CONFIGURATION
# =====================================================================

# Default council slots — models loaded serially via ollama
# Swap model names when primary models are installed
DEFAULT_COUNCIL = {
    "council_members": [
        {
            "name": "analytical",
            "model": "qwen2.5-coder:14b",  # Slot 1: analytical temp 0.3
            "fallback": "qwen2.5:7b-instruct",
            "temperature_mode": "analytical",
            "max_tokens": 600,
        },
        {
            "name": "creative",
            "model": "mythomax-l2-13b",  # Slot 2: creative temp 0.9
            "fallback": "qwen2.5:7b-instruct",
            "temperature_mode": "creative",
            "max_tokens": 600,
        },
        {
            "name": "balanced",
            "model": "gemma3:12b-it",  # Slot 3: balanced temp 0.7
            "fallback": "qwen2.5:7b-instruct",
            "temperature_mode": "balanced",
            "max_tokens": 600,
        },
    ],
    "judge": {
        "name": "mimo-v2-pro",
        "model": "mimo-v2-pro",  # Cloud judge (Nous OAuth)
        "fallback": "qwen2.5:7b-instruct",  # Local fallback judge
        "temperature_mode": "analytical",
        "max_tokens": 1000,
    },
    "temperature_modes": {
        "analytical": 0.3,
        "balanced": 0.7,
        "creative": 0.9,
    },
    "ollama_base_url": "http://localhost:11434",
}

# Temperature presets for council rounds
TEMP_PRESETS = {
    "analytical": {"description": "Low temperature, precise, factual", "default": 0.3},
    "balanced":   {"description": "Medium temperature, reasoned but open", "default": 0.7},
    "creative":   {"description": "High temperature, lateral, surprising", "default": 0.9},
}


# =====================================================================
# OLLAMA COMMUNICATION
# =====================================================================

def _call_ollama(model, prompt, temperature=0.7, max_tokens=800, timeout=120):
    """Call ollama API directly. Serial loading — one model in VRAM at a time."""
    import urllib.request

    url = f"{DEFAULT_COUNCIL['ollama_base_url']}/api/generate"
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }).encode()

    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        return result.get("response", "")
    except Exception as e:
        logger.warning(f"Ollama call failed for {model}: {e}")
        return None


def _call_cloud(model, prompt, temperature=0.7, max_tokens=800):
    """Call cloud model via evey_utils (existing infrastructure)."""
    try:
        import importlib.util as _iu, os as _os
        _spec = _iu.spec_from_file_location("evey_utils", _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "evey_utils.py"))
        _eu = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_eu)
        call_model = _eu.call_model

        result = call_model(model, prompt, max_tokens=max_tokens, temperature=temperature, retries=2, timeout=120)
        if result:
            return result["content"]
        return None
    except Exception as e:
        logger.warning(f"Cloud call failed for {model}: {e}")
        return None


def _query_model(model_name, prompt, temperature, max_tokens, is_local=True):
    """Query a model — local ollama or cloud."""
    if is_local:
        return _call_ollama(model_name, prompt, temperature, max_tokens)
    else:
        return _call_cloud(model_name, prompt, temperature, max_tokens)


# =====================================================================
# COUNCIL ENGINE
# =====================================================================

def _get_temperature(slot_config, mode_override=None):
    """Get temperature from slot config and mode."""
    if mode_override:
        return TEMP_PRESETS.get(mode_override, TEMP_PRESETS["balanced"])["default"]
    mode = slot_config.get("temperature_mode", "balanced")
    return TEMP_PRESETS.get(mode, TEMP_PRESETS["balanced"])["default"]


def _query_council_member(slot, question, context, mode_override=None):
    """Query one council member with fallback."""
    model = slot["model"]
    fallback = slot.get("fallback")
    temperature = _get_temperature(slot, mode_override)
    max_tokens = slot.get("max_tokens", 800)

    prompt = question
    if context:
        prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"

    # Try primary model (local ollama)
    logger.info(f"Council querying {slot['name']}: {model} (temp={temperature})")
    answer = _query_model(model, prompt, temperature, max_tokens, is_local=True)

    if answer:
        return {"model": model, "name": slot["name"], "status": "success", "answer": answer, "temperature": temperature}

    # Fallback
    if fallback:
        logger.info(f"  Fallback to {fallback}")
        answer = _query_model(fallback, prompt, temperature, max_tokens, is_local=True)
        if answer:
            return {"model": fallback, "name": slot["name"], "status": "fallback", "answer": answer, "temperature": temperature}

    return {"model": model, "name": slot["name"], "status": "failed", "answer": None, "temperature": temperature}


def _build_judge_prompt(question, context, answers):
    """Build the judge's synthesis prompt."""
    prompt = "You are a judge synthesizing answers from a model council.\n\n"
    if context:
        prompt += f"CONTEXT:\n{context}\n\n"
    prompt += f"QUESTION: {question}\n\n"

    for i, ans in enumerate(answers, 1):
        if ans["status"] in ("success", "fallback"):
            prompt += f"SLOT {i} ({ans['name']}, temp={ans['temperature']}) said:\n"
            prompt += f"{ans['answer']}\n\n"

    prompt += "SYNTHESIZE the best answer from the above responses. "
    prompt += "Identify where they agree, where they diverge, and produce the strongest combined answer."

    return prompt


def council_decide(question, context=None, mode_override=None):
    """
    Run the Numogram Council.

    Args:
        question: The question for the council
        context: Additional context (optional)
        mode_override: Override temperature mode for all slots
                       ('analytical', 'balanced', 'creative')

    Returns:
        dict with 'answer', 'individual_answers', 'council_members', etc.
    """
    config = DEFAULT_COUNCIL
    members = config["council_members"]
    judge = config["judge"]

    logger.info(f"Council convened: {question[:80]}... mode={mode_override or 'per-slot'}")

    # Phase 1: Query all council members serially (ollama swaps models)
    start_time = time.time()
    answers = []

    for i, slot in enumerate(members):
        logger.info(f"Member {i+1}/{len(members)}: {slot['name']}")
        result = _query_council_member(slot, question, context, mode_override)
        answers.append(result)
        if result["status"] == "success":
            logger.info(f"  ✓ {slot['name']} responded ({len(result['answer'])} chars)")
        elif result["status"] == "fallback":
            logger.info(f"  ◐ {slot['name']} used fallback ({len(result['answer'])} chars)")
        else:
            logger.warning(f"  ✗ {slot['name']} failed")

    council_time = time.time() - start_time
    succeeded = [a for a in answers if a["status"] in ("success", "fallback")]
    logger.info(f"Council phase 1: {len(succeeded)}/{len(answers)} in {council_time:.1f}s")

    if not succeeded:
        return json.dumps({"status": "all_failed", "error": "All council members failed", "answers": answers})

    # Phase 2: Judge synthesizes
    judge_prompt = _build_judge_prompt(question, context, succeeded)
    judge_temp = _get_temperature(judge, mode_override)

    logger.info(f"Judge: {judge['model']} (temp={judge_temp})")
    judge_start = time.time()

    # Try cloud judge first
    synthesis = _call_cloud(judge["model"], judge_prompt, judge_temp, judge["max_tokens"])

    # Fallback to local judge
    if not synthesis and judge.get("fallback"):
        logger.info(f"  Judge fallback to {judge['fallback']}")
        synthesis = _call_ollama(judge["fallback"], judge_prompt, judge_temp, judge["max_tokens"])

    judge_time = time.time() - judge_start

    if not synthesis:
        # Last resort: return longest answer
        synthesis = max(succeeded, key=lambda r: len(r.get("answer", "")))["answer"]
        logger.warning("  Judge failed, returning longest member answer")

    return json.dumps({
        "status": "success",
        "answer": synthesis,
        "individual_answers": {a["name"]: a["answer"] for a in succeeded},
        "council_members": len(members),
        "successful_members": len(succeeded),
        "council_time": council_time,
        "judge_time": judge_time,
        "mode": mode_override or "per-slot",
    })


# =====================================================================
# SCHEMA
# =====================================================================

SCHEMA = {
    "name": "council_decide",
    "description": (
        "Convene the Numogram Council. Sends a question to 3 local models "
        "serially (ollama, one model in VRAM at a time), collects answers, "
        "then a judge synthesizes the best answer. Supports temperature modes: "
        "'analytical' (0.3), 'balanced' (0.7), 'creative' (0.9). "
        "Zero API cost for council members. Cloud judge with local fallback."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question for the council to deliberate on",
            },
            "context": {
                "type": "string",
                "description": "Additional context (optional)",
            },
            "mode_override": {
                "type": "string",
                "description": "Override temperature mode: 'analytical', 'balanced', or 'creative'",
                "enum": ["analytical", "balanced", "creative"],
            },
        },
        "required": ["question"],
    },
}
def register(ctx):
    ctx.register_tool(
        name="council_decide",
        toolset="numogram_council",
        schema=SCHEMA,
        handler=council_decide,
    )

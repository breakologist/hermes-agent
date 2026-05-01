#!/usr/bin/env python3
"""
Numogram Council — Modular Deliberation System (v3.0, 2026-04-25)

Modes:
  stress       — canonical test battery (palindromic, syzygy, triangular, cross-system, controversy)
  tetralogue   — four-voice deliberation (Oracle, Builder, Writer, Gamer) + Oracle judge
  calibration  — generation → validation loop with hyperstition scoring

Backend-agnostic: supports ollama and OpenAI-compatible APIs (llama.cpp, vLLM, LM Studio).
Configure slots, modes, and voice→slot mapping in ~/.hermes/council/config.yaml.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

# Load shared LLM utilities (evey_utils) for unified model calls across providers
try:
    import importlib.util as _iu
    import os as _os
    _spec = _iu.spec_from_file_location(
        "evey_utils",
        _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "evey_utils.py")
    )
    _eu = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_eu)
    call_model = _eu.call_model
except Exception:
    call_model = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (deferred loading)
# ---------------------------------------------------------------------------

COUNCIL_ROOT = Path.home() / '.hermes' / 'council'
CONFIG_PATH = COUNCIL_ROOT / 'config.yaml'
VOICES_DIR = COUNCIL_ROOT / 'voices'
MODES_DIR = COUNCIL_ROOT / 'modes'
TESTS_DIR = COUNCIL_ROOT / 'tests'

# Lazily loaded cache
_CONFIG_CACHE: Dict[str, Any] | None = None
_VOICE_CACHE: Dict[str, dict] = {}

def _load_yaml() -> Any:
    """Import yaml on demand, with clear error if missing."""
    try:
        import yaml as _y
        return _y
    except ImportError as e:
        raise ImportError(
            "PyYAML is required for numogram-council plugin. "
            "Install with: pip install pyyaml"
        ) from e

def _get_config() -> Dict[str, Any]:
    """Load and cache council config."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _y = _load_yaml()
        with open(CONFIG_PATH) as cfg_f:
            _CONFIG_CACHE = _y.safe_load(cfg_f)
    return _CONFIG_CACHE

def _load_voice(name: str) -> dict:
    cfg = _get_config()
    _y = _load_yaml()
    vp = VOICES_DIR / cfg['voices'][name]['file']
    with open(vp) as f:
        data = _y.safe_load(f)
    data['voice_name'] = name
    data['zone'] = cfg['voices'][name]['zone']
    return data

# Temperature presets for stress-mode temperature_mode strings
TEMP_PRESETS = {"analytical": 0.3, "balanced": 0.7, "creative": 0.9}
# Voice-based temperature presets
VOICE_TEMP = {"oracle": 0.3, "builder": 0.5, "writer": 0.7, "gamer": 0.9}

# Voice mapping shortcuts (load on first use)
_VOICE_CACHE: Dict[str, dict] = {}

def _get_voice(name: str) -> dict:
    if name not in _VOICE_CACHE:
        _VOICE_CACHE[name] = _load_voice(name)
    return _VOICE_CACHE[name]

# ---------------------------------------------------------------------------
# Slot definitions
# ---------------------------------------------------------------------------

# Stress-mode slots: three reasoning modes using same local model
COUNCIL_SLOTS_STRESS: List[dict] = [
    {
        "name": "analytical",
        "model": "Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF:Q5_K_M",
        "provider": "openai",
        "base_url": "http://localhost:8080",
        "temperature_mode": "analytical",
        "max_tokens": 600,
        "fallback": None,
        "description": "Analytical reasoning (low temp, stepwise)",
    },
    {
        "name": "creative",
        "model": "Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF:Q5_K_M",
        "provider": "openai",
        "base_url": "http://localhost:8080",
        "temperature_mode": "creative",
        "max_tokens": 600,
        "fallback": None,
        "description": "Creative lateral thinking (high temp)",
    },
    {
        "name": "balanced",
        "model": "Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF:Q5_K_M",
        "provider": "openai",
        "base_url": "http://localhost:8080",
        "temperature_mode": "balanced",
        "max_tokens": 600,
        "fallback": None,
        "description": "Balanced synthesis (mid temp)",
    },
]

# Tetralogue-mode slots: lazy construction (depends on config)
def _get_tetralogue_slots() -> List[dict]:
    """Build tetralogue slots on first use (after config is available)."""
    cfg = _get_config()
    voice_order = cfg.get('tetralogue_mapping', {})
    return [
        {
            "name": "oracle",
            "voice": voice_order.get('member_0', 'oracle'),
            "model": "stepfun/step-3.5-flash",
            "provider": "openai",
            "base_url": "https://inference-api.nousresearch.com/v1",
            "max_tokens": 1200,
            "fallback": None,
            "description": "Oracle voice (Zone 0)",
        },
        {
            "name": "builder",
            "voice": voice_order.get('member_1', 'builder'),
            "model": "stepfun/step-3.5-flash",
            "provider": "openai",
            "base_url": "https://inference-api.nousresearch.com/v1",
            "max_tokens": 1200,
            "fallback": None,
            "description": "Builder voice (Zone 5)",
        },
        {
            "name": "writer",
            "voice": voice_order.get('member_2', 'writer'),
            "model": "stepfun/step-3.5-flash",
            "provider": "openai",
            "base_url": "https://inference-api.nousresearch.com/v1",
            "max_tokens": 1200,
            "fallback": None,
            "description": "Writer voice (Zone 3)",
        },
        {
            "name": "gamer",
            "voice": voice_order.get('member_3', 'gamer'),
            "model": "stepfun/step-3.5-flash",
            "provider": "openai",
            "base_url": "https://inference-api.nousresearch.com/v1",
            "max_tokens": 1200,
            "fallback": None,
            "description": "Gamer voice (Zone 7)",
        },
    ]

# Judge slot: Oracle by default (Zone 0 synthesist)
JUDGE_SLOT = {
    "name": "oracle_judge",
    "model": "stepfun/step-3.5-flash",
    "provider": "openai",
    "base_url": "https://inference-api.nousresearch.com/v1",
    "max_tokens": 2000,
    "fallback": None,
    "description": "Oracle judge (Zone 0 synthesis)",
}

# Import yaml for config reading
import yaml


def _session_id() -> str:
    pid = os.getpid()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{pid}"


def _temp(slot: dict, override: str | None = None) -> float:
    """
    Resolve temperature for a slot.
    Order: explicit override → slot.temperature_mode (stress) → voice.temp (tetralogue) → 0.7
    """
    if override:
        return TEMP_PRESETS.get(override, 0.7)
    mode = slot.get("temperature_mode")
    if mode in TEMP_PRESETS:
        return TEMP_PRESETS[mode]
    # Voice-based temp (tetralogue slots carry a 'voice' key)
    voice = slot.get("voice")
    if voice in VOICE_TEMP:
        return VOICE_TEMP[voice]
    return 0.7


# ---------------------------------------------------------------------------
# Backend dispatch
# ---------------------------------------------------------------------------

def _call_ollama(prompt: str, model: str, temp: float, tokens: int, base_url: str) -> str | None:
    import urllib.request, urllib.error
    url = f"{base_url}/api/generate"
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temp, "num_predict": tokens},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read())
            return data.get("response", "")
    except urllib.error.HTTPError as e:
        logger.warning(f"Ollama HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        logger.warning(f"Ollama error: {e}")
    return None


def _call_openai(prompt: str, model: str, temp: float, tokens: int, base_url: str) -> str | None:
    import urllib.request, urllib.error
    url = f"{base_url}/v1/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temp,
        "max_tokens": tokens,
        "stream": False,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        logger.warning(f"OpenAI-compat HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        logger.warning(f"OpenAI-compat error: {e}")
    return None


def _call_backend(slot: dict, prompt: str, temp: float, tokens: int) -> str | None:
    provider = slot.get("provider", "ollama").lower()
    model = slot["model"]
    if provider == "ollama":
        base = slot.get("base_url", "http://localhost:11434/v1")
        return _call_ollama(prompt, model, temp, tokens, base)
    # Direct OpenAI-compatible call (e.g., StepFun) with bearer token
    base = slot.get("base_url", "https://inference-api.nousresearch.com/v1").rstrip('/')
    api_key = slot.get("api_key") or os.environ.get("STEPFUN_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No API key found for non-ollama provider. Set STEPFUN_API_KEY or OPENAI_API_KEY.")
        return None
    try:
        import urllib.request
        import urllib.error
        url = f"{base}/chat/completions"
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": tokens,
            "stream": False,
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        logger.warning(f"HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        logger.warning(f"OpenAI-compat error: {e}")
    return None


def _member_prompt(slot: dict, question: str, context: str | None, mode: str) -> str:
    """
    Build prompt for a council member.
    Stress mode: generic role-based prompt (no voice YAMLs).
    Tetralogue/Calibration: inject voice system_prompt from voices/*.yaml.
    """
    lines = []

    if mode == "stress":
        desc = slot.get("description", "Analyst")
        lines.append(f"Role: {slot['name']} — {desc}")
        lines.append("")
        if context:
            lines.append(f"Context:\\n{context}\\n")
        lines.append(f"Question:\\n{question}\\n")
        lines.append("Provide your full perspective. Avoid echoing other members.")
    else:
        # Tetralogue or Calibration — use voice YAML
        voice_name = slot.get("voice") or slot.get("name")
        voice = _get_voice(voice_name)
        lines.append(f"You are the {voice_name.upper()} (Zone {voice['zone']}).")
        lines.append(f"Style: {voice['style']}")
        lines.append("")
        lines.append(voice['system_prompt'].strip())
        lines.append("")
        if context:
            lines.append(f"Relevant context:\\n{context}\\n")
        lines.append(f"Question: {question}")
        lines.append("")
        lines.append("Answer concisely but with full reasoning. End with a one-sentence summary.")

    return "\n".join(lines)


def _judge_prompt(question: str, context: str | None, answers: List[dict], mode: str) -> str:
    """Build judge prompt. Uses Oracle voice for tetralogue/calibration; generic for stress."""
    if mode in ("tetralogue", "calibration"):
        judge_voice = _get_voice("oracle")
        parts = [
            "You are the ORACLE JUDGE (Zone 0 — Void).",
            "You perceive closed loops and pattern completions.",
            "",
            "Question: " + question,
            "",
        ]
        if context:
            parts.append(f"Context:\\n{context}\\n")
        parts.append("Member responses:\\n")
        for a in answers:
            parts.append(f"--- {a['name']} ({a.get('voice','unknown')}) ---\\n{a['answer']}\\n")
        parts.append(
            "Synthesize a final answer that transcends partiality. "
            "Return:\n"
            "1. Synthesis (2–3 sentences)\n"
            "2. One-sentence kernel of unavoidable truth\n"
            "3. Flag any unresolved tensions\n"
            "Begin your conclusion with 'Final conclusion:'"
        )
        return "\n".join(parts)
    else:
        # Generic judge for stress mode (keeps original behaviour)
        parts = ["You are a judge synthesizing multiple analyses into a final answer.", ""]
        if context:
            parts.append(f"Context:\\n{context}\\n")
        parts.append(f"Question: {question}\\n")
        parts.append("Member responses:\\n")
        for a in answers:
            parts.append(f"--- {a['name']} (temp={a['temperature']}) ---\\n{a['answer']}\\n")
        parts.append(
            "Synthesise an integrated final answer. Highlight consensus and note any residual "
            "uncertainty. Begin your conclusion with 'Final conclusion:'"
        )
        return "\n".join(parts)




# ---------------------------------------------------------------------------
# Hyperstitional auto-context injector (Tier-1 + Tier-2 canonical dictionaries)
# ---------------------------------------------------------------------------
def _build_calibration_dictionary_context() -> str:
    """Compose a compact markdown reference from the Tier-2 Expanded Dictionary.
    Used automatically in calibration mode when no explicit context is provided."""
    raw_path = Path.home() / ".hermes" / "obsidian" / "hermetic" / "raw" / "AQ_Numogram_Expanded_Dictionary.md"
    if not raw_path.exists():
        return ""
    try:
        content = raw_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    lines = content.splitlines()

    # Locate "## 2. Major Currents" section
    start = end = None
    for idx, line in enumerate(lines):
        if line.startswith("## 2. Major Currents"):
            start = idx
        elif start is not None and line.startswith("## ") and "Major Currents" not in line:
            end = idx
            break
    if start is None or end is None:
        return ""

    from collections import defaultdict
    entries = []
    current_section = "Unspecified"
    for line in lines[start:end]:
        m_sec = re.match(r"^###\s+(.+)$", line)
        if m_sec:
            current_section = m_sec.group(1).strip()
            continue
        aq_match = re.search(r"=\s*(\d{1,4})\s*AQ", line)
        if aq_match and line.lstrip().startswith("-"):
            phrase = re.sub(r"^\s*-\s*", "", line)
            phrase = re.sub(r"\s*=\s*\d{1,4}\s*AQ.*$", "", phrase).strip()
            # Strip surrounding quotes
            if phrase and phrase[0] in ('"', '"', '"') and phrase[-1] in ('"', '"', '"'):
                phrase = phrase[1:-1]
            entries.append({"section": current_section, "phrase": phrase, "aq": aq_match.group(1)})

    if not entries:
        return ""

    by_sec = defaultdict(list)
    for e in entries:
        by_sec[e["section"]].append(e)

    out = ["## Canonical AQ Reference (Tier-1 + Tier-2 Synthesis)"]
    for sec in sorted(by_sec.keys()):
        out.append(f"\n### {sec}")
        for e in by_sec[sec][:7]:  # cap at 7 entries per section
            out.append(f"- {e['phrase']} = {e['aq']} AQ")
    out.append("")
    return "\n".join(out).strip()

# ---------------------------------------------------------------------------
# Tool entry point
# ---------------------------------------------------------------------------

def council_decide(
    question: str,
    context: str | None = None,
    mode: str = "stress",          # stress | tetralogue | calibration
    mode_override: str | None = None,  # kept for backward-compat; maps to stress temp override
    **kwargs,
) -> str:
    """
    Convene the Numogram Council — mode-based deliberative engine.
    Returns JSON string with full result structure.
    """
    start = time.time()
    ws = Path.home() / ".hermes" / "council" / "workspace" / _session_id()
    ws.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------
    # Resolve active mode & slot selection
    # --------------------------------------------------------------------
    active_mode = mode  # stress | tetralogue | calibration

    if active_mode == "stress":
        slots = COUNCIL_SLOTS_STRESS
        # mode_override accepted for temp control (analytical/balanced/creative)
        temp_mode_override = mode_override
    elif active_mode == "tetralogue":
        slots = _get_tetralogue_slots()
        temp_mode_override = None  # voice-based temps
    elif active_mode == "calibration":
        # Calibration uses tetralogue slots but selects voice subsets in two phases
        slots = _get_tetralogue_slots()

        # Hyperstitional auto-context: synthesize from Tier-1/2 canonical dictionaries
        # if the caller did not supply explicit context. This grounds AQ candidates in the
        # expanded AQ lattice before generation begins.
        if not context:
            try:
                context = _build_calibration_dictionary_context()
            except Exception as exc:
                logger.warning(f"Calibration auto-context failed: {exc}")
        temp_mode_override = None
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown mode '{mode}'. Valid: stress, tetralogue, calibration",
        }, ensure_ascii=False)

    # --------------------------------------------------------------------
    # Phase dispatcher
    # --------------------------------------------------------------------
    if active_mode == "calibration":
        # Two-phase: generation (oracle+writer+builder) → validation (oracle+builder+gamer)
        # Select voice subsets from the tetralogue slots
        all_slots = slots  # these are tetralogue slots
        gen_voice_names = ["oracle", "writer", "builder"]
        val_voice_names = ["oracle", "builder", "gamer"]

        def pick_slots(names: list) -> list:
            picked = []
            for s in all_slots:
                if s.get("voice", s["name"]) in names:
                    picked.append(s)
            return picked

        gen_slots = pick_slots(gen_voice_names)
        val_slots = pick_slots(val_voice_names)

        # Workspace for calibration phases
        ws_gen = ws / "generation"
        ws_val = ws / "validation"
        ws_gen.mkdir(parents=True, exist_ok=True)
        ws_val.mkdir(parents=True, exist_ok=True)

        # -----------------
        # Phase 1 — Generation
        # -----------------
        generation_question = (
            f"Propose 3 candidate AQ values for: '{question}'.\\n\\n"
            "For each candidate provide:\\n"
            "1. AQ integer (0-35)\\n"
            "2. One-sentence cipher rationale (Base-36, digital root, zone fit)\\n"
            "3. One-sentence hyperstitional hook\\n\\n"
            "Rank from strongest cipher to weakest."
        )
        gen_members = []
        for slot in gen_slots:
            temp = _temp(slot, None)
            prompt = _member_prompt(slot, generation_question, context, "calibration")
            (ws_gen / f"prompt_{slot['name']}.txt").write_text(prompt, encoding="utf-8")
            ans = _call_backend(slot, prompt, temp, slot.get("max_tokens", 600))
            status = "success" if ans else "failed"
            if ans:
                (ws_gen / f"answer_{slot['name']}.json").write_text(json.dumps({"answer": ans}, ensure_ascii=False), encoding="utf-8")
            gen_members.append({
                "name": slot["name"],
                "voice": slot.get("voice", slot["name"]),
                "answer": ans,
                "status": status,
            })

        # Compile candidates placeholder string for validation phase
        # (we can't parse the responses reliably, so we inject raw answers and let validator aggregate synthetically)
        # In practice the agent would post-process; here we just forward the answers as context
        val_context_addendum = "\\n\\n".join(
            f"--- Candidate set from {m['name']} ---\\n{m['answer']}" for m in gen_members if m["status"] == "success"
        )
        validation_question = (
            f"Evaluate these AQ candidates for '{question}':\\n\\n"
            f"{val_context_addendum}\\n\\n"
            "Score each candidate 0-10 on:\\n"
            "- Cipher compliance (Base-36 + digital root) — weight 0.4\\n"
            "- Hyperstition potency — weight 0.3\\n"
            "- Exploitability — weight 0.3\\n\\n"
            "Flag any cipher-irreparable failures.\\n"
            "Return JSON only:\\n"
            '{"candidates": [{"aq": N, "cipher_score": 0-10, "hyp_score": 0-10, "exploit_score": 0-10, "flags": ["..."]}]}'
        )
        val_members = []
        for slot in val_slots:
            temp = _temp(slot, None)
            prompt = _member_prompt(slot, validation_question, context, "calibration")
            (ws_val / f"prompt_{slot['name']}.txt").write_text(prompt, encoding="utf-8")
            ans = _call_backend(slot, prompt, temp, slot.get("max_tokens", 800))
            status = "success" if ans else "failed"
            if ans:
                (ws_val / f"answer_{slot['name']}.json").write_text(json.dumps({"answer": ans}, ensure_ascii=False), encoding="utf-8")
            val_members.append({
                "name": slot["name"],
                "voice": slot.get("voice", slot["name"]),
                "answer": ans,
                "status": status,
            })

        # -----------------
        # Phase 3 — Oracle Judge synthesis
        # -----------------
        judge_context = (
            "Generation phase answers:\\n" + "\\n".join(
                f"[{m['name']}] {m['answer'][:200]}" for m in gen_members if m["status"] == "success"
            ) + "\\n\\nValidation phase answers:\\n" + "\\n".join(
                f"[{m['name']}] {m['answer'][:200]}" for m in val_members if m["status"] == "success"
            )
        )
        judge_prompt_text = _judge_prompt(
            question=f"AQ calibration for '{question}'",
            context=judge_context,
            answers=[
                {"name": m["name"], "answer": m["answer"], "voice": m["voice"]}
                for m in gen_members + val_members if m["status"] == "success"
            ],
            mode="calibration"
        )
        (ws / "judge_prompt.txt").write_text(judge_prompt_text, encoding="utf-8")
        judge_start = time.time()
        judge_ans = _call_backend(JUDGE_SLOT, judge_prompt_text, _temp(JUDGE_SLOT, None), JUDGE_SLOT.get("max_tokens", 1200))
        judge_secs = time.time() - judge_start
        if not judge_ans:
            judge_ans = "Judge synthesis failed."

        council_secs = time.time() - start
        final = judge_ans.strip()
        (ws / "final.json").write_text(json.dumps({"answer": final}, ensure_ascii=False, indent=2), encoding="utf-8")

        return json.dumps({
            "status": "success",
            "answer": final,
            "individual_answers": {
                **{f"gen_{m['name']}": m["answer"] for m in gen_members},
                **{f"val_{m['name']}": m["answer"] for m in val_members},
            },
            "council_members": len(gen_slots) + len(val_slots),
            "successful_members": sum(1 for m in gen_members+val_members if m["status"]=="success"),
            "council_time": council_secs,
            "judge_time": judge_secs,
            "mode": "calibration",
            "workspace": str(ws),
            "meta": {
                "generation_members": [s["name"] for s in gen_slots],
                "validation_members": [s["name"] for s in val_slots],
            }
        }, ensure_ascii=False)

    # Standard single-phase modes (stress, tetralogue)
    member_results: List[dict] = []
    for slot in slots:
        temp = _temp(slot, temp_mode_override if active_mode == "stress" else None)
        prompt = _member_prompt(slot, question, context, active_mode)
        (ws / f"prompt_{slot['name']}.txt").write_text(prompt, encoding="utf-8")
        ans = _call_backend(slot, prompt, temp, slot.get("max_tokens", 600))
        if ans:
            member_results.append({
                "name": slot["name"],
                "model": slot["model"],
                "status": "success",
                "answer": ans,
                "temperature": temp,
                "voice": slot.get("voice", slot["name"]),
            })
            (ws / f"answer_{slot['name']}.json").write_text(
                json.dumps({"answer": ans}, ensure_ascii=False), encoding="utf-8"
            )
            logger.info(f"Council {slot['name']} ✓ {len(ans)} chars")
        else:
            fb = slot.get("fallback")
            if fb:
                fb_slot = {**slot, "model": fb}
                ans = _call_backend(fb_slot, prompt, temp, slot.get("max_tokens", 600))
                if ans:
                    member_results.append({
                        "name": slot["name"],
                        "model": fb,
                        "status": "fallback",
                        "answer": ans,
                        "temperature": temp,
                        "voice": slot.get("voice", slot["name"]),
                    })
                    continue
            member_results.append({
                "name": slot["name"],
                "model": slot["model"],
                "status": "failed",
                "answer": None,
                "temperature": temp,
                "voice": slot.get("voice", slot["name"]),
            })
            logger.warning(f"Council {slot['name']} failed")

    succeeded = [a for a in member_results if a["status"] == "success"]
    council_secs = time.time() - start

    if not succeeded:
        return json.dumps({
            "status": "all_failed",
            "error": "No council members responded",
            "individual_answers": {},
            "council_members": len(slots),
            "successful_members": 0,
            "council_time": council_secs,
            "judge_time": 0,
            "mode": active_mode,
        }, ensure_ascii=False)

    # --- Judge ---
    judge_text = _judge_prompt(question, context, succeeded, active_mode)
    (ws / "judge_prompt.txt").write_text(judge_text, encoding="utf-8")
    judge_start = time.time()
    judge_ans = _call_backend(JUDGE_SLOT, judge_text, _temp(JUDGE_SLOT, None), JUDGE_SLOT.get("max_tokens", 1000))
    judge_secs = time.time() - judge_start

    if not judge_ans and JUDGE_SLOT.get("fallback"):
        fb_judge = {**JUDGE_SLOT, "model": JUDGE_SLOT["fallback"]}
        judge_ans = _call_backend(fb_judge, judge_text, _temp(JUDGE_SLOT, None), JUDGE_SLOT.get("max_tokens", 1000))

    if not judge_ans:
        judge_ans = max(succeeded, key=lambda a: len(a["answer"]))["answer"]

    final = judge_ans.strip()
    (ws / "final.json").write_text(json.dumps({"answer": final}, ensure_ascii=False, indent=2), encoding="utf-8")

    return json.dumps({
        "status": "success",
        "answer": final,
        "individual_answers": {a["name"]: a["answer"] for a in succeeded},
        "council_members": len(slots),
        "successful_members": len(succeeded),
        "council_time": council_secs,
        "judge_time": judge_secs,
        "mode": active_mode,
        "workspace": str(ws),
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Mode-specific runners
# ---------------------------------------------------------------------------

def _run_calibration(question: str, context: str | None, ws: Path, slots: List[dict]) -> dict:
    """Two-phase calibration: generation (oracle+writer+builder) → validation (oracle+builder+gamer)."""
    from .modes import calibration as calib_mode
    # Delegate to calibration.py module
    return calib_mode.run(
        topic=question,
        context=context,
        slots=slots,
        judge_slot=JUDGE_SLOT,
        call_backend=_call_backend,
        build_prompt=_member_prompt,
        ws=ws,
    )


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

SCHEMA = {
    "name": "council_decide",
    "description": (
        "Convene the Numogram Council — multi-mode deliberative engine. "
        "Modes: stress (canonical test battery), tetralogue (four-voice deliberation), "
        "calibration (generation → validation with hyperstition scoring). "
        "Backend-agnostic: works with Ollama and any OpenAI-compatible API "
        "(llama.cpp, vLLM, LM Studio). Voice definitions and mode parameters in ~/.hermes/council/config.yaml."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question/prompt for the council"
            },
            "context": {
                "type": "string",
                "description": "Optional additional context (future: auto-ingested from wiki/Obsidian)"
            },
            "mode": {
                "type": "string",
                "enum": ["stress", "tetralogue", "calibration"],
                "description": "Deliberation mode. stress: test battery; tetralogue: four-voice; calibration: AQ candidate generation + validation",
                "default": "stress"
            },
            "mode_override": {
                "type": "string",
                "enum": ["analytical", "balanced", "creative"],
                "description": "Override temperature mode (stress mode only; ignored in tetralogue/calibration)",
            },
        },
        "required": ["question"],
    },
}


def _slash_handler(raw_args: str) -> str:
    """
    /council <question>               → stress mode (default)
    /council-stress <question>        → stress mode explicit
    /council-tetralogue <question>    → tetralogue mode
    /council-calibrate <topic>        → calibration mode
    """
    args = raw_args.strip()
    if not args:
        return (
            "Numogram Council slash commands:\\n"
            "  /council <question>        — stress test (default)\\n"
            "  /council-stress <question> — explicit stress test\\n"
            "  /council-tetralogue <q>   — four-voice deliberation\\n"
            "  /council-calibrate <topic> — hyperstition calibration loop"
        )

    # Detect which slash command was used via command name mapping
    # The gateway calls this handler per-command; we receive the command name via kwargs in real use.
    # Here we just parse raw_args: if it starts with a known subcommand, consume it.
    parts = args.split(maxsplit=1)
    subcmd = parts[0].lower()
    question = parts[1] if len(parts) > 1 else ""

    # Map subcommand to mode
    if subcmd in ("council", "council-stress", "stress"):
        mode = "stress"
        if subcmd == "council" and not question:
            return "Usage: /council <question>"
    elif subcmd in ("council-tetralogue", "tetralogue"):
        mode = "tetralogue"
        if not question:
            return "Usage: /council-tetralogue <question>"
    elif subcmd in ("council-calibrate", "calibrate"):
        mode = "calibration"
        if not question:
            return "Usage: /council-calibrate <topic>"
    else:
        return f"Unknown council command: {subcmd}. Use /council, /council-stress, /council-tetralogue, or /council-calibrate."

    try:
        result = council_decide(question=question, mode=mode)
        parsed = json.loads(result)
        if parsed.get("status") == "success":
            out = f"Council ✓ {mode} mode\\n"
            out += f"Time: {parsed['council_time']:.1f}s council + {parsed['judge_time']:.1f}s judge\\n"
            out += f"Members: {parsed['successful_members']}/{parsed['council_members']} responded\\n\\n"
            out += "MEMBER RESPONSES:\\n"
            for name, ans in parsed["individual_answers"].items():
                out += f"\\n{'='*60}\\n[{name}]\\n{ans[:300]}" + ("…" if len(ans) > 300 else "") + "\\n"
            out += f"\\n{'='*60}\\nJUDGE SYNTHESIS:\\n{parsed['answer']}"
            # Include workspace path for later audit
            out += f"\\n\\n[Workspace: {parsed.get('workspace','?')}]"
            return out
        else:
            return f"[Council error {mode}]: {parsed.get('error','unknown')}"
    except Exception as e:
        return f"[Council exception {mode}]: {e}"


def register(ctx):
    ctx.register_tool(
        name="council_decide",
        toolset="numogram_council",
        schema=SCHEMA,
        handler=council_decide,
    )
    # Register slash commands for each mode
    commands = [
        ("council", "Convene the Numogram Council (stress mode by default)", "<question>"),
        ("council-stress", "Run a stress-test battery item", "<question>"),
        ("council-tetralogue", "Four-voice deliberation (Oracle/Builder/Writer/Gamer)", "<question>"),
        ("council-calibrate", "Hyperstition calibration: generate + validate AQ candidates", "<topic>"),
    ]
    for name, desc, args in commands:
        ctx.register_command(
            name=name,
            handler=_make_slash_handler(name),
            description=desc,
            args_hint=args,
        )


def _make_slash_handler(command_name: str):
    """Factory: returns a slash handler bound to a specific command name."""
    def handler(raw_args: str) -> str:
        args = raw_args.strip()
        if not args:
            help_texts = {
                "council": "Usage: /council <question>",
                "council-stress": "Usage: /council-stress <question>",
                "council-tetralogue": "Usage: /council-tetralogue <question>",
                "council-calibrate": "Usage: /council-calibrate <topic>",
            }
            return help_texts[command_name]

        # Map command → mode
        mode_map = {
            "council": "stress",
            "council-stress": "stress",
            "council-tetralogue": "tetralogue",
            "council-calibrate": "calibration",
        }
        mode = mode_map[command_name]

        try:
            result = council_decide(question=args, mode=mode)
            parsed = json.loads(result)
            if parsed.get("status") == "success":
                out = f"Council ✓ {mode} mode\\n"
                out += f"Time: {parsed['council_time']:.1f}s council + {parsed['judge_time']:.1f}s judge\\n"
                out += f"Members: {parsed['successful_members']}/{parsed['council_members']} responded\\n\\n"
                out += "MEMBER RESPONSES:\\n"
                for name, ans in parsed["individual_answers"].items():
                    out += f"\\n{'='*60}\\n[{name}]\\n{ans[:400]}" + ("…" if len(ans) > 400 else "") + "\\n"
                out += f"\\n{'='*60}\\nJUDGE SYNTHESIS:\\n{parsed['answer']}"
                out += f"\\n\\n[Workspace: {parsed.get('workspace','?')}]"
                return out
            else:
                return f"[Council error {mode}]: {parsed.get('error','unknown')}"
        except Exception as e:
            return f"[Council exception {mode}]: {e}"
    return handler

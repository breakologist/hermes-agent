"""Numogram Context Engine — a lens on the decimal labyrinth.

Lives in plugins/context_engine/numogram/. Activated by setting
`context.engine: numogram` in config.yaml.

The engine maintains numogram state across turns and exposes zone/AQ/syzygy
tools directly to the agent. It has a configurable focus level that acts
as a lens:

    focus=0  off     — behaves like default compressor (transparent)
    focus=1  soft    — light numogram awareness, no tool injection
    focus=2  medium  — protects numogram messages, injects tools
    focus=3  hard    — aggressive protection + zone context injection

Adjust focus at runtime with the `numogram_focus` tool or by setting
`context.numogram.focus` in config.yaml (default: 1).
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── AQ Cipher (Base-36: A=10, ..., Z=35) ─────────────────────────────

AQ_MAP = {}
for i in range(10):
    AQ_MAP[str(i)] = i
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    AQ_MAP[c] = i + 10
    AQ_MAP[c.lower()] = i + 10

# ─── Zone Data ─────────────────────────────────────────────────────────

ZONE_DATA = {
    0: {"name": "Void", "region": "plex", "mesh": "0000", "spinal": "Coccygeal"},
    1: {"name": "Stability", "region": "torque", "mesh": "0001", "spinal": "Lumbar"},
    2: {"name": "Separation", "region": "torque", "mesh": "0003", "spinal": "Lumbar"},
    3: {"name": "Release", "region": "warp", "mesh": "0007", "spinal": "Solar"},
    4: {"name": "Catastrophe", "region": "torque", "mesh": "0100", "spinal": "Solar"},
    5: {"name": "Pressure", "region": "torque", "mesh": "0101", "spinal": "Cardiac"},
    6: {"name": "Abstraction", "region": "warp", "mesh": "0110", "spinal": "Cardiac"},
    7: {"name": "Blood", "region": "torque", "mesh": "0111", "spinal": "Pharyngeal"},
    8: {"name": "Multiplicity", "region": "torque", "mesh": "1000", "spinal": "Cavernous"},
    9: {"name": "Iron Core", "region": "plex", "mesh": "0511", "spinal": "Sacral"},
}

SYZYGIES = {
    frozenset({4, 5}): {"current": 1, "demon": "Katak", "region": "torque"},
    frozenset({3, 6}): {"current": 3, "demon": "Djynxx", "region": "warp"},
    frozenset({2, 7}): {"current": 5, "demon": "Oddubb", "region": "torque"},
    frozenset({1, 8}): {"current": 7, "demon": "Murrumur", "region": "torque"},
    frozenset({0, 9}): {"current": 9, "demon": "Uttunul", "region": "plex"},
}

# Gate cumulation: Gt(n) = C(n) = n(n-1)/2
# Gates are named by their cumulation value, not the pair sum.
GATE_CUMULATION = {
    1: 0,   # C(1) = 0
    2: 1,   # C(2) = 1
    3: 3,   # C(3) = 3
    4: 6,   # C(4) = 6
    5: 10,  # C(5) = 10
    6: 15,  # C(6) = 15
    7: 21,  # C(7) = 21
    8: 28,  # C(8) = 28
    9: 36,  # C(9) = 36
}

# ─── AQ Functions ──────────────────────────────────────────────────────

def aq_value(text: str) -> int:
    """A=10...Z=35, digits face value, non-alphanumeric ignored."""
    return sum(AQ_MAP.get(ch, 0) for ch in text)

def digital_root(n: int) -> int:
    """Digital root mod 9. 0 stays 0."""
    if n == 0:
        return 0
    return 1 + (n - 1) % 9

def zone_of(n: int) -> int:
    """Map a number to its numogram zone (digital root)."""
    return digital_root(n)

def cumulative(n: int) -> int:
    """C(n) = n(n-1)/2 — gate cumulation."""
    return n * (n - 1) // 2

def is_triangular(n: int) -> Optional[int]:
    """Check if n is triangular T(k)=k(k+1)/2. Returns k or None."""
    disc = 8 * n + 1
    if disc < 1:
        return None
    root = int(disc ** 0.5)
    if root * root == disc and (root - 1) % 2 == 0:
        return (root - 1) // 2
    return None

def get_syzygy(zone_a: int, zone_b: int) -> Optional[Dict]:
    """Look up the syzygy (demon bond) between two zones."""
    return SYZYGIES.get(frozenset({zone_a, zone_b}))

# ─── Numogram Keywords (for message scanning) ─────────────────────────

NUMOGRAM_PATTERNS = [
    r"\bzone[\s-]?\d\b",
    r"\bnumogram\b",
    r"\bsyzygy\b",
    r"\bsyzygies\b",
    r"\bcurrent\b.*\b[sS]urge|[Hh]old|[Ss]ink|[Ww]arp|[Pp]lex\b",
    r"\b[Kk]atak|[Dd]jynxx|[Oo]ddubb|[Mm]urrumur|[Uu]ttunul\b",
    r"\b[Aa][Qq]\b",
    r"\b(?:alphanumeric\s+)?[Qq]abbala\b",
    r"\bdigital\s+root\b",
    r"\btriangular\b",
    r"\bgate[\s]?\d\b",
    r"\bwarp\b|\btorque\b|\bplex\b",
    r"\b[Pp]lexing\b",
    r"\b[Nn]umogram\b",
    r"\b[Ll]abyrinth\b",
    r"\b[Cc][Cc][Rr][Uu]\b",
    r"\b[Ll]and\b.*\b[Nn]umogram|[Qq]abbala\b",
]
_NUMOGRAM_RE = re.compile("|".join(NUMOGRAM_PATTERNS), re.IGNORECASE)

def is_numogram_relevant(text: str) -> bool:
    """Check if text contains numogram-related content."""
    if not text:
        return False
    return bool(_NUMOGRAM_RE.search(text))


# ─── The Context Engine ───────────────────────────────────────────────

class NumogramContextEngine:
    """A lens on the decimal labyrinth.

    Adjustable focus controls how aggressively numogram context is
    preserved and injected. At focus=0, behaves identically to the
    default built-in compressor (fully transparent). At focus=3,
    numogram content is maximally protected and zone context is
    injected every turn.
    """

    # Identity
    @property
    def name(self) -> str:
        return "numogram"

    # Token state (read by run_agent.py)
    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0
    last_total_tokens: int = 0
    threshold_tokens: int = 0
    context_length: int = 0
    compression_count: int = 0

    # Compaction parameters
    threshold_percent: float = 0.75
    protect_first_n: int = 3
    protect_last_n: int = 6

    def __init__(self):
        # Numogram state
        self.active_zone: int = 9  # Start at Plex (the hub)
        self.recent_calculations: List[Dict] = []
        self.session_id: Optional[str] = None
        self._focus: int = 1  # Default: soft

        # Config file for focus persistence
        self._config_path = Path.home() / ".hermes" / "config.yaml"

    @property
    def focus(self) -> int:
        """Current focus level 0-3."""
        return self._focus

    @focus.setter
    def focus(self, level: int):
        self._focus = max(0, min(3, level))

    # ─── Core Interface ────────────────────────────────────────────────

    def update_from_response(self, usage: Dict[str, Any]) -> None:
        """Track token usage from API responses."""
        self.last_prompt_tokens = usage.get("prompt_tokens", 0)
        self.last_completion_tokens = usage.get("completion_tokens", 0)
        self.last_total_tokens = usage.get("total_tokens",
                                            self.last_prompt_tokens + self.last_completion_tokens)

    def should_compress(self, prompt_tokens: int = None) -> bool:
        """Check if compaction should fire."""
        tokens = prompt_tokens or self.last_prompt_tokens
        if self.context_length <= 0:
            return False
        return tokens >= self.threshold_tokens

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int = None,
    ) -> List[Dict[str, Any]]:
        """Compact messages with numogram-aware protection.

        Strategy by focus level:
          0 (off)     — pass-through (caller handles compression)
          1 (soft)    — lightly protect numogram messages, standard compression
          2 (medium)  — stronger protection, inject zone header
          3 (hard)    — aggressive protection, inject full zone context

        In all modes, system messages and recent turns are always preserved.
        Numogram-relevant messages get extra protection slots based on focus.
        """
        if self._focus == 0 or len(messages) <= self.protect_first_n + self.protect_last_n + 4:
            # Focus off or too few messages to compress meaningfully
            return messages

        self.compression_count += 1

        # Always protect: system messages, first N, last N
        protected: List[Dict[str, Any]] = []
        body: List[Dict[str, Any]] = []

        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        # First and last N non-system messages
        head = non_system[:self.protect_first_n]
        tail = non_system[-self.protect_last_n:]
        middle = non_system[self.protect_first_n:-self.protect_last_n]

        if not middle:
            return messages  # Nothing to compress

        # Scan middle for numogram relevance
        numogram_msgs = []
        other_msgs = []
        for msg in middle:
            content = msg.get("content", "")
            if isinstance(content, str) and is_numogram_relevant(content):
                numogram_msgs.append(msg)
            else:
                other_msgs.append(msg)

        # Protection budget scales with focus
        # focus 1: protect 2 numogram messages
        # focus 2: protect 5 numogram messages
        # focus 3: protect all numogram messages
        protection_budget = {1: 2, 2: 5, 3: 999}
        budget = protection_budget.get(self._focus, 2)

        preserved_numogram = numogram_msgs[:budget]
        discardable = other_msgs + numogram_msgs[budget:]

        # Inject zone context header at focus 2+
        if self._focus >= 2:
            zone_info = self._build_zone_context()
            context_msg = {
                "role": "system",
                "content": f"[Numogram Context] {zone_info}"
            }
            protected = system_msgs + [context_msg] + head + preserved_numogram + tail
        else:
            protected = system_msgs + head + preserved_numogram + tail

        # Log what was discarded
        if discardable:
            logger.debug(
                "Numogram engine: kept %d numogram msgs, discarded %d others (focus=%d)",
                len(preserved_numogram), len(discardable), self._focus
            )

        return protected

    # ─── Tools ─────────────────────────────────────────────────────────

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Expose numogram tools to the agent.

        Focus 0-1: no tools (transparent)
        Focus 2-3: full tool suite
        """
        if self._focus < 2:
            return []

        return [
            {
                "type": "function",
                "function": {
                    "name": "aq_calc",
                    "description": "Calculate AQ (Alphanumeric Qabbala) value for text. Returns AQ value, digital root, zone, and zone name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to calculate AQ value for (letters A-Z, digits 0-9)"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "zone_lookup",
                    "description": "Look up numogram zone data by zone number (0-9). Returns zone name, region, mesh, and spinal mapping.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zone": {
                                "type": "integer",
                                "description": "Zone number 0-9"
                            }
                        },
                        "required": ["zone"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "syzygy_find",
                    "description": "Find the syzygy (demon bond) between two numogram zones. Returns current, demon name, and region.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zone_a": {
                                "type": "integer",
                                "description": "First zone (0-9)"
                            },
                            "zone_b": {
                                "type": "integer",
                                "description": "Second zone (0-9)"
                            }
                        },
                        "required": ["zone_a", "zone_b"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "numogram_focus",
                    "description": "Adjust the numogram context engine focus level. 0=off (transparent), 1=soft (light awareness), 2=medium (tools + protection), 3=hard (aggressive). Returns current focus state.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "level": {
                                "type": "integer",
                                "description": "Focus level 0-3",
                                "enum": [0, 1, 2, 3]
                            }
                        },
                        "required": ["level"]
                    }
                }
            },
        ]

    def handle_tool_call(self, name: str, args: Dict[str, Any], **kwargs) -> str:
        """Handle numogram tool calls from the agent."""
        try:
            if name == "aq_calc":
                text = args.get("text", "")
                val = aq_value(text)
                dr = digital_root(val)
                zone = zone_of(val)
                info = ZONE_DATA.get(zone, {})
                result = {
                    "text": text,
                    "aq_value": val,
                    "digital_root": dr,
                    "zone": zone,
                    "zone_name": info.get("name", "Unknown"),
                    "region": info.get("region", ""),
                    "is_triangular": is_triangular(val),
                }
                # Track calculation
                self.recent_calculations.append(result)
                if len(self.recent_calculations) > 20:
                    self.recent_calculations = self.recent_calculations[-20:]
                # Update active zone
                self.active_zone = zone
                return json.dumps(result)

            elif name == "zone_lookup":
                zone = args.get("zone", 0)
                if zone not in ZONE_DATA:
                    return json.dumps({"error": f"Invalid zone: {zone}. Must be 0-9."})
                info = ZONE_DATA[zone].copy()
                info["zone"] = zone
                # Find syzygies involving this zone
                info["syzygies"] = []
                for pair, data in SYZYGIES.items():
                    if zone in pair:
                        other = next(z for z in pair if z != zone)
                        info["syzygies"].append({
                            "paired_zone": other,
                            "current": data["current"],
                            "demon": data["demon"],
                            "region": data["region"],
                        })
                return json.dumps(info)

            elif name == "syzygy_find":
                a = args.get("zone_a", 0)
                b = args.get("zone_b", 0)
                syzygy = get_syzygy(a, b)
                if syzygy is None:
                    # Check if same zone (self-syzygy is Zone 9 plexing)
                    if a == b == 9:
                        return json.dumps({
                            "zones": [9, 9],
                            "current": 9,
                            "demon": "Uttunul",
                            "region": "plex",
                            "note": "Self-plexing — Zone 9 folds into itself"
                        })
                    return json.dumps({
                        "error": f"No syzygy between zones {a} and {b}. "
                                 f"Valid syzygies: 4::5, 3::6, 2::7, 1::8, 0::9"
                    })
                result = {"zones": sorted([a, b]), **syzygy}
                return json.dumps(result)

            elif name == "numogram_focus":
                new_level = args.get("level", self._focus)
                old_level = self._focus
                self.focus = new_level
                return json.dumps({
                    "previous_focus": old_level,
                    "current_focus": self._focus,
                    "focus_label": ["off", "soft", "medium", "hard"][self._focus],
                    "tools_active": self._focus >= 2,
                    "protection_level": {0: "none", 1: "light", 2: "strong", 3: "maximum"}[self._focus],
                })

            else:
                return json.dumps({"error": f"Unknown tool: {name}"})

        except Exception as e:
            logger.error("Numogram tool error (%s): %s", name, e)
            return json.dumps({"error": str(e)})

    # ─── Session Lifecycle ─────────────────────────────────────────────

    def on_session_start(self, session_id: str, **kwargs) -> None:
        """Load numogram state on session start."""
        self.session_id = session_id
        self.recent_calculations = []

        # Try to read focus from config
        try:
            import yaml
            if self._config_path.exists():
                with open(self._config_path) as f:
                    config = yaml.safe_load(f) or {}
                ctx = config.get("context", {})
                numo = ctx.get("numogram", {})
                self._focus = max(0, min(3, numo.get("focus", 1)))
                self.active_zone = numo.get("active_zone", 9)
        except Exception as e:
            logger.debug("Could not read numogram config: %s", e)

        logger.info(
            "Numogram engine started (session=%s, focus=%d, zone=%d)",
            session_id, self._focus, self.active_zone
        )

    def on_session_end(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Persist numogram state on session end."""
        # Scan final messages for zone references to update active_zone
        for msg in reversed(messages):
            content = msg.get("content", "")
            if isinstance(content, str):
                zones = re.findall(r"\bzone[\s-]?(\d)\b", content, re.IGNORECASE)
                if zones:
                    self.active_zone = int(zones[-1])
                    break

        logger.info(
            "Numogram engine ended (session=%s, zone=%d, calcs=%d)",
            session_id, self.active_zone, len(self.recent_calculations)
        )

    def on_session_reset(self) -> None:
        """Reset per-session state."""
        super().on_session_reset() if hasattr(super(), 'on_session_reset') else None
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0
        self.compression_count = 0
        self.recent_calculations = []

    # ─── Status ────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return status for display/logging."""
        base = {
            "last_prompt_tokens": self.last_prompt_tokens,
            "threshold_tokens": self.threshold_tokens,
            "context_length": self.context_length,
            "usage_percent": (
                min(100, self.last_prompt_tokens / self.context_length * 100)
                if self.context_length else 0
            ),
            "compression_count": self.compression_count,
        }
        # Add numogram-specific status
        base["numogram"] = {
            "focus": self._focus,
            "focus_label": ["off", "soft", "medium", "hard"][self._focus],
            "active_zone": self.active_zone,
            "zone_name": ZONE_DATA.get(self.active_zone, {}).get("name", "?"),
            "recent_calculations": len(self.recent_calculations),
        }
        return base

    # ─── Model Switch Support ──────────────────────────────────────────

    def update_model(
        self,
        model: str,
        context_length: int,
        base_url: str = "",
        api_key: str = "",
        provider: str = "",
    ) -> None:
        """Update on model switch."""
        self.context_length = context_length
        self.threshold_tokens = int(context_length * self.threshold_percent)

    # ─── Helpers ────────────────────────────────────────────────────────

    def _build_zone_context(self) -> str:
        """Build a compact zone context string for injection."""
        zone = self.active_zone
        info = ZONE_DATA.get(zone, {})
        lines = [
            f"Active Zone: {zone} ({info.get('name', '?')})",
            f"Region: {info.get('region', '?')}, Mesh: {info.get('mesh', '?')}",
        ]

        # Add recent calculations summary
        if self.recent_calculations:
            recent = self.recent_calculations[-5:]
            calcs = ", ".join(
                f"{c['text']}={c['aq_value']}(z{c['zone']})"
                for c in recent
            )
            lines.append(f"Recent AQ: {calcs}")

        # Add syzygy info for active zone
        syzygies = []
        for pair, data in SYZYGIES.items():
            if zone in pair:
                other = next(z for z in pair if z != zone)
                syzygies.append(f"{other}::{data['demon']}")
        if syzygies:
            lines.append(f"Syzygies: {', '.join(syzygies)}")

        return " | ".join(lines)


# ─── Plugin Registration ───────────────────────────────────────────────

def register(ctx):
    """Register the numogram context engine with the plugin system."""
    ctx.register_context_engine(NumogramContextEngine())

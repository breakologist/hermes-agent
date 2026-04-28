#!/usr/bin/env python3
"""
numogram-audio/mod-writer Plugin — Hermes Agent integration.

Exposes a slash command (/mod-writer) and a tool (numogram_mod_writer)
that generate Protracker modules using numogram-native mappings.
"""

import sys
import subprocess
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_CLI_PATH = _THIS_DIR / 'cli.py'


def _run_cli(args_str: str) -> str:
    """Execute the mod-writer CLI with the given raw argument string."""
    cmd = [sys.executable, str(_CLI_PATH)] + args_str.split()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=_THIS_DIR,
        )
        if proc.returncode == 0:
            return proc.stdout.strip() or "✓ mod-writer executed"
        return (
            f"✗ mod-writer failed (exit {proc.returncode})\n"
            f"STDERR:\n{proc.stderr[:800]}"
        )
    except subprocess.TimeoutExpired:
        return "[mod-writer error] timed out after 60s"
    except Exception as exc:
        return f"[mod-writer error] {exc}"


def _slash_handler(raw_args: str) -> str:
    """Slash command: /mod-writer [--zone N] [--gate N] [--current A|B|C] [--title NAME] [--output PATH]"""
    if not raw_args.strip():
        return (
            "Numogram MOD Writer\n"
            "Usage: /mod-writer --zone N --gate N --current A|B|C [--title NAME] [--output FILE]\n"
            "Example: /mod-writer --zone 3 --gate 6 --current A --title \"Warp Tune\" --output warp.mod\n"
            "Flags:\n"
            "  --zone N     Zone (1-9)\n"
            "  --gate N     Gate (0-36)\n"
            "  --current A|B|C\n"
            "  --title NAME Song title (max 20 chars)\n"
            "  --output FILE Output .mod path"
        )
    return _run_cli(raw_args)


def register(ctx):
    """Register slash command and AI-callable tool."""
    # Slash command for TUI
    ctx.register_command(
        name="mod_writer",
        handler=_slash_handler,
        description="Generate a Protracker .mod module from numogram zone/gate/current",
        args_hint="--zone N --gate N --current A|B|C [--title NAME] [--output FILE]",
    )

    # Optional tool for AI orchestration (minimal implementation)
    ctx.register_tool(
        name="numogram_mod_writer",
        description="Generate a tracker module given numogram parameters",
        toolset="numogram_audio",
        schema={
            "type": "object",
            "properties": {
                "zone": {"type": "integer", "minimum": 1, "maximum": 9, "description": "Numogram zone 1-9"},
                "gate": {"type": "integer", "minimum": 0, "maximum": 36, "description": "Gate 0-36"},
                "current": {"type": "string", "enum": ["A", "B", "C"], "description": "Current (A=square, B=triangle, C=noise)"},
                "title": {"type": "string", "maxLength": 20, "description": "Song title (optional)"},
                "output": {"type": "string", "description": "Output .mod filename"},
                "syzygy": {"type": "boolean", "description": "Add syzygy harmony on channels 1-3"},
                "syzygy_channels": {"type": "integer", "minimum": 1, "maximum": 3, "default": 3},
                "entropy": {"type": "number", "minimum": 0, "maximum": 1, "description": "Entropy injection rate"},
                "entropy_seed": {"type": "integer", "description": "Entropy RNG seed"},
                "triangular": {"type": "boolean", "description": "Pattern length = triangular number of zone"},
                "aq_seed": {"type": "string", "description": "AQ seed string to constrain gate progression"},
                "rows": {"type": "integer", "minimum": 1, "maximum": 64, "default": 16}
            },
            "required": ["zone", "gate", "current", "output"],
        },
        handler=lambda params: _run_cli(
            f"--zone {params['zone']} --gate {params['gate']} --current {params['current']} "
            f"--title {params.get('title','HermesTrack')} --output {params['output']}"
            + (f" --syzygy" if params.get('syzygy') else "")
            + (f" --syzygy-channels {params.get('syzygy_channels',3)}" if params.get('syzygy') else "")
            + (f" --entropy {params['entropy']}" if params.get('entropy') is not None else "")
            + (f" --entropy-seed {params['entropy_seed']}" if params.get('entropy_seed') is not None else "")
            + (f" --triangular" if params.get('triangular') else "")
            + (f" --aq-seed {params['aq_seed']}" if params.get('aq_seed') else "")
            + (f" --rows {params['rows']}" if params.get('rows', 16) != 16 else "")
        )
            f"--zone {params['zone']} --gate {params['gate']} --current {params['current']} "
            f"--title {params.get('title','HermesTrack')} --output {params['output']}"
            + (f" --syzygy" if params.get('syzygy') else "")
            + (f" --syzygy-channels {params['syzygy_channels']}" if params.get('syzygy') else "")
            + (f" --entropy {params['entropy']}" if params.get('entropy') is not None else "")
            + (f" --entropy-seed {params['entropy_seed']}" if params.get('entropy_seed') is not None else "")
            + (f" --triangular" if params.get('triangular') else "")
            + (f" --aq-seed {params['aq_seed']}" if params.get('aq_seed') else "")
            + (f" --rows {params['rows']}" if params.get('rows', 16) != 16 else "")
        )} --output {params['output']}"
        ),
    )

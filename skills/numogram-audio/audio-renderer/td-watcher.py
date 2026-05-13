#!/usr/bin/env python3
"""
TouchDesigner file-watcher for numogram-audio output.

Watches a directory for newly generated .wav and _spectrogram.png files,
then writes a compact TD status JSON that TouchDesigner can poll via
File In DAT or a simple HTTP endpoint.

Usage:
    python3 td-watcher.py --dir ~/numogram/outputs --poll 2.0
    (Ctrl-C to stop)

The watcher writes `td_state.json` into --dir after each change.
TD project should read this file and update Text TOPs / Movie File In TOPs.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

STATE_FILE = "td_state.json"


def scan_dir(dir_path: Path) -> Dict:
    """Scan dir for most recent WAV + spectrogram pair, merge TD status + analysis."""
    wav_files = sorted(dir_path.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
    spec_files = sorted(dir_path.glob("*_spectrogram.png"), key=lambda p: p.stat().st_mtime, reverse=True)

    latest_wav = wav_files[0] if wav_files else None
    latest_spec = spec_files[0] if spec_files else None

    if latest_wav:
        base = latest_wav.stem
        td_json  = dir_path / f"{base}.json"
        ana_json = dir_path / f"{base}_analysis.json"
        mod_path = dir_path / f"{base}.mod"

        entry = {
            "wav": str(latest_wav.resolve()),
            "wav_mtime": latest_wav.stat().st_mtime,
            "spectrogram": str(latest_spec.resolve()) if latest_spec else None,
            "mod": str(mod_path.resolve()) if mod_path.exists() else None,
            "title": base,
        }

        if td_json.exists():
            try:
                with open(td_json) as f:
                    meta = json.load(f)
                entry.update(meta)
            except Exception as e:
                print(f"⚠ Could not read {td_json}: {e}", file=sys.stderr)

        if ana_json.exists():
            try:
                with open(ana_json) as f:
                    analysis = json.load(f)
                entry["analysis"] = analysis
                quality = analysis.get("quality", "unknown")
                entry["quality"] = quality
                entry["health_color"] = {
                    "pass": "#00ff00",
                    "warning": "#ffaa00",
                    "fail": "#ff0000",
                }.get(quality, "#ffffff")
            except Exception as e:
                print(f"⚠ Could not read {ana_json}: {e}", file=sys.stderr)

        return {"latest": entry, "count": len(wav_files)}
    else:
        return {"latest": None, "count": 0}


def write_state(state: Dict, out_path: Path):
    tmp = out_path.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, out_path)


def main():
    p = argparse.ArgumentParser(description="TD file-watcher for numogram-audio output")
    p.add_argument("--dir", default=".", help="Directory to watch (default: current)")
    p.add_argument("--poll", type=float, default=2.0, help="Poll interval seconds (default 2.0)")
    p.add_argument("--state-file", default=STATE_FILE, help="Output state filename")
    args = p.parse_args()

    watch_dir = Path(args.dir).expanduser().resolve()
    state_path = watch_dir / args.state_file

    print(f"👀 Watching {watch_dir} — state → {state_path}")
    last_mtime = 0

    try:
        while True:
            state = scan_dir(watch_dir)
            current_mtime = state["latest"]["wav_mtime"] if state["latest"] else 0
            if current_mtime != last_mtime:
                write_state(state, state_path)
                title = state['latest']['title'] if state['latest'] else 'empty'
                print(f"  ↻ Updated: {title}")
                last_mtime = current_mtime
            time.sleep(args.poll)
    except KeyboardInterrupt:
        print("\n👋 Stopped.")


if __name__ == "__main__":
    main()

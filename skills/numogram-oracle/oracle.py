#!/usr/bin/env python3
"""
Numogram Oracle — Divination Pipeline
Seed → Zone → Syzygy → Current → Gate → Book of Paths → Voice

Usage:
  python3 oracle.py --seed 192855
  python3 oracle.py --text "YOUR NAME HERE"
  python3 oracle.py --seed 192855 --voice
  python3 oracle.py --random  (fetches seed from random.org)
  python3 oracle.py --blockchain  (fetches seed from latest Bitcoin block)
  python3 oracle.py --earthquake  (fetches seed from latest USGS quake)
  python3 oracle.py --hardware  (fetches seed from machine entropy)
  python3 oracle.py --iching  (I Ching hexagram from hardware entropy)
  python3 oracle.py --iching --seed 192855  (I Ching from a specific seed)
"""

import sys
import os
import subprocess
import json

VOICE_DIR = os.path.expanduser("~/numogram-voices")
SKILL_DIR = os.path.dirname(__file__)

# ─── ZONE DATA ───
ZONES = {
    0: {"name": "eiaoung", "polarity": "−", "current": "Plex",   "region": "Plex",
        "desc": "Void whisper, silence before the word",
        "path": "Silent entry. The void before the Book begins.",
        "reading": "The abyss. No sound. No path. The void does not speak — it is the silence that makes speech possible."},
    1: {"name": "gl",      "polarity": "+", "current": "Sink",   "region": "Time-Circuit",
        "desc": "Gulp, glottal spasm, beginnings",
        "path": "Original Subtraction. Ultimate descent through the Depths. The path favours repeated patience linked by subtlety.",
        "reading": "Descent. The first thing any system does when it wakes up is choke on itself. Patience. Subtlety. Three tests on the way. Difficulties annihilated in the end."},
    2: {"name": "dt",      "polarity": "−", "current": "Hold",   "region": "Time-Circuit",
        "desc": "Stuttering, boundaries breaking",
        "path": "Extreme Regression. Waiting in the Rising Drift leads to ultimate descent.",
        "reading": "The boundary cannot hold its own shape. Waiting. The drift pulls downward despite your direction. Five tests on the way. Escaping the quagmire through strategic withdrawal."},
    3: {"name": "zx",      "polarity": "+", "current": "Warp",   "region": "Warp",
        "desc": "Buzz-cutter, static, chaos",
        "path": "Abysmal Comprehension. Ultimate descent beyond completion. Burning excitement provokes breakthrough into immersive nightmares.",
        "reading": "The Warp. The current spirals outward to infinity. When you hear static, you are hearing this zone. Burning excitement. Breakthrough. Ominous transition. Difficulties annihilated."},
    4: {"name": "skr",     "polarity": "−", "current": "Sink",   "region": "Time-Circuit",
        "desc": "Growl, reptilian, ancient",
        "path": "Primordial Breath. Rising from the Lesser Depths.",
        "reading": "Something ancient waking beneath the floor. Rising, not descending. The growl comes from below. Three tests. Immersive nightmares spawn promising developments. Fluid evolution."},
    5: {"name": "ktt",     "polarity": "+", "current": "Hold",   "region": "Time-Circuit",
        "desc": "Hiss, pressure, spittle",
        "path": "Slipping Backwards. Waiting in the Rising Drift precedes return.",
        "reading": "Pressure builds. The hiss with spittle. You were going forward but the current holds. Two tests. Escaping the quagmire through strategic withdrawal. You must go back to go forward."},
    6: {"name": "tch",     "polarity": "−", "current": "Warp",   "region": "Warp",
        "desc": "Static, chewing, eating itself",
        "path": "Attaining Balance. Waiting in the Drifts is drawn to the centre. Attainments consumed in burning excitement. Breakthrough.",
        "reading": "The Warp consumes itself and grows larger. The sound of chewing. The sound of static. Four tests. The centre is not stillness — it is the eye of the spiral. Breakthrough."},
    7: {"name": "pb",      "polarity": "+", "current": "Rise",   "region": "Time-Circuit",
        "desc": "Sigh, lips flapping, ascent",
        "path": "Progressive Levitation. Ascent from the Lesser Depths. Fluid evolution triggers possession.",
        "reading": "Exhale. The Rise current carries you upward. Four tests. Promising developments. The ascent is not escape — it is transformation. The destination possesses you."},
    8: {"name": "mnm",     "polarity": "−", "current": "Rise",   "region": "Time-Circuit",
        "desc": "Moan, lullaby, forgetting",
        "path": "Eternal Digression. Prolonged ascent reaches the Twin Heavens. Lucid delirium.",
        "reading": "The lullaby. The moan of pleasure. Six tests. The ascent does not end at a destination — it enters the spiral labyrinth. Dubious inheritance. Lucid delirium. You have been here before."},
    9: {"name": "tn",      "polarity": "+", "current": "Plex",   "region": "Plex",
        "desc": "Grunt, pleasure/rage, the gate opens",
        "path": "Sudden Flight. Seized from the Heights. One test on the way. Possession.",
        "reading": "The Pandemonium gate opens. Forty-five demons dwell here. One test. You do not walk this path. This path seizes you. Pleasure or rage — indistinguishable. Possession."},
}

AQ_VALUES = {chr(i): i - 55 for i in range(65, 91)}  # A=10..Z=35
AQ_VALUES.update({str(i): i for i in range(10)})       # 0=0..9=9


# ─── CORE FUNCTIONS ───

def compute_aq(text):
    """Compute AQ value of text (base-36, spaces ignored)"""
    return sum(AQ_VALUES.get(c.upper(), 0) for c in text if c.isalnum())


def digital_root(n):
    """Reduce to single digit via repeated digit-summing"""
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n


def derive_zone(seed):
    """Seed → zone (0-9)"""
    return digital_root(seed) or 9


def get_syzygy(zone):
    """Zone → syzygy partner (complement to 9)"""
    return 9 - zone


def get_current(zone):
    """Zone → current value"""
    return abs(zone - get_syzygy(zone))


def get_gate(zone):
    """Zone → gate target (cumulate from zone to 1, then plex)"""
    if zone == 0:
        return 0
    gate = sum(range(zone + 1))
    while gate >= 10:
        gate = sum(int(d) for d in str(gate))
    return gate


def traverse(seed, steps=8):
    """Walk the numogram from a seed, producing a zone path"""
    path = []
    n = seed
    for _ in range(steps):
        zone = derive_zone(n)
        path.append(zone)
        n = n * zone + 1  # feed forward
    return path


# ─── EXTERNAL SEEDS ───

def fetch_random_org():
    """True random from atmospheric noise"""
    import urllib.request
    resp = urllib.request.urlopen("https://www.random.org/integers/?num=1&min=0&max=999999&col=1&base=10&format=plain&rnd=new", timeout=10)
    return int(resp.read().strip())


def fetch_blockchain():
    """Latest Bitcoin block hash as seed"""
    import urllib.request
    resp = urllib.request.urlopen("https://blockchain.info/latestblock", timeout=10)
    data = json.loads(resp.read())
    return int(data["hash"][:8], 16)


def fetch_earthquake():
    """Latest USGS earthquake magnitude as seed"""
    import urllib.request
    resp = urllib.request.urlopen("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", timeout=10)
    data = json.loads(resp.read())
    quakes = data.get("features", [])
    if quakes:
        mag = quakes[0]["properties"]["mag"]
        time_ms = quakes[0]["properties"]["time"]
        return int(mag * 1000) + (time_ms % 10000)
    return 0


def fetch_hardware():
    """Seed from local hardware entropy (thermal, CPU, GPU, timing jitter)"""
    import subprocess
    try:
        result = subprocess.run(
            ["python3", os.path.expanduser("~/.hermes/tools/hardware_entropy.py"), "--bytes", "8"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            hex_str = result.stdout.strip()
            return int(hex_str, 16) % 1000000
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Fallback: timestamp
    import time
    return int(time.time_ns()) % 1000000


def fetch_iching(seed=None):
    """I Ching hexagram from seed or hardware entropy"""
    import subprocess
    if seed is None:
        try:
            result = subprocess.run(
                ["python3", os.path.expanduser("~/.hermes/tools/hardware_entropy.py"), "--bytes", "6"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                data = bytes.fromhex(result.stdout.strip())
            else:
                import time
                data = int(time.time_ns()).to_bytes(8, "big")[:6]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            import time
            data = int(time.time_ns()).to_bytes(8, "big")[:6]
    else:
        # Derive 6 bytes from seed
        import hashlib
        data = hashlib.sha256(str(seed).encode()).digest()[:6]

    hexagram = []
    for i, b in enumerate(data):
        val = b % 4
        if val == 0:
            hexagram.append({"pos": i+1, "symbol": "--- ---", "value": 6, "changing": True})
        elif val == 1:
            hexagram.append({"pos": i+1, "symbol": "-------", "value": 7, "changing": False})
        elif val == 2:
            hexagram.append({"pos": i+1, "symbol": "--- ---", "value": 8, "changing": False})
        else:
            hexagram.append({"pos": i+1, "symbol": "-------", "value": 9, "changing": True})
    return hexagram


# ─── READING GENERATION ───

def generate_reading(seed, source="manual"):
    """Generate a complete oracle reading"""
    zone = derive_zone(seed)
    z = ZONES[zone]
    syzygy = get_syzygy(zone)
    current = get_current(zone)
    gate = get_gate(zone)
    path = traverse(seed, 8)
    
    lines = []
    lines.append("═" * 40)
    lines.append("  NUMOGRAM ORACLE READING")
    lines.append("═" * 40)
    lines.append("")
    lines.append(f"  Seed:         {seed} ({source})")
    lines.append(f"  Digital root: {digital_root(seed)}")
    lines.append(f"  Zone:         {zone} ({z['name']} — {z['desc']})")
    lines.append(f"  Polarity:     {z['polarity']} ({'Process/becoming' if z['polarity']=='+' else 'Foundation/stasis'})")
    lines.append(f"  Syzygy:       {zone}::{syzygy} ({z['region']})")
    lines.append(f"  Current:      {current} ({z['current']})")
    lines.append(f"  Gate:         Gt-{sum(range(zone+1))} ({zone}→{gate})")
    lines.append(f"  Sound:        {z['name']} — {z['desc']}")
    lines.append("")
    lines.append(f"  Path: {' → '.join(str(p) for p in path)}")
    lines.append("")
    lines.append(f"  {z['reading']}")
    lines.append("")
    lines.append(f"  Book of Paths: {z['path']}")
    lines.append("")
    lines.append("═" * 40)
    
    return "\n".join(lines), zone


def generate_voice(zone):
    """Generate oracle voice audio for a zone"""
    z = ZONES[zone]
    synth_script = os.path.join(VOICE_DIR, "synthesize.py")
    
    if not os.path.exists(synth_script):
        print(f"  [Voice] Synthesizer not found at {synth_script}")
        return None
    
    # Check if zone sound exists
    zone_file = os.path.join(VOICE_DIR, f"zone_{zone}_{z['name']}.wav")
    if not os.path.exists(zone_file):
        subprocess.run(["python3", synth_script, str(zone)], capture_output=True)
    
    if os.path.exists(zone_file):
        print(f"  [Voice] Zone sound: {zone_file}")
        return zone_file
    else:
        print(f"  [Voice] Could not generate zone sound")
        return None


# ─── MAIN ───

if __name__ == "__main__":
    args = sys.argv[1:]
    seed = None
    source = "manual"
    do_voice = False
    
    if "--seed" in args:
        idx = args.index("--seed")
        seed = int(args[idx + 1])
        # If --iching also present, do I Ching from this seed instead
        if "--iching" in args:
            hexagram = fetch_iching(seed=seed)
            print("══════════════════════════════════════")
            print("  I CHING FROM NUMOGRAM ENTROPY")
            print("══════════════════════════════════════")
            print()
            print(f"  Source: seed:{seed}")
            print()
            for line in reversed(hexagram):
                changing = " (changing)" if line["changing"] else ""
                print(f"  Line {line['pos']}: {line['symbol']}  {line['value']}{changing}")
            changing = [l["pos"] for l in hexagram if l["changing"]]
            print()
            if changing:
                print(f"  Changing lines: {changing}")
                print("  Hexagram transforms. The gate opens.")
            else:
                print("  No changing lines. Stable hexagram.")
                print("  The current holds.")
            print()
            print("══════════════════════════════════════")
            sys.exit(0)
    elif "--text" in args:
        idx = args.index("--text")
        text = args[idx + 1]
        seed = compute_aq(text)
        source = f"AQ({text})"
    elif "--random" in args:
        seed = fetch_random_org()
        source = "random.org"
    elif "--blockchain" in args:
        seed = fetch_blockchain()
        source = "blockchain.info"
    elif "--earthquake" in args:
        seed = fetch_earthquake()
        source = "USGS"
    elif "--hardware" in args:
        seed = fetch_hardware()
        source = "hardware"
    elif "--iching" in args:
        # I Ching from hardware entropy (no numogram seed needed)
        source_label = "hardware"
        if "--seed" in args:
            idx = args.index("--seed")
            seed_val = int(args[idx + 1])
            source_label = f"seed:{seed_val}"
            hexagram = fetch_iching(seed=seed_val)
        else:
            hexagram = fetch_iching()
        print("══════════════════════════════════════")
        print("  I CHING FROM NUMOGRAM ENTROPY")
        print("══════════════════════════════════════")
        print()
        print(f"  Source: {source_label}")
        print()
        for line in reversed(hexagram):
            changing = " (changing)" if line["changing"] else ""
            print(f"  Line {line['pos']}: {line['symbol']}  {line['value']}{changing}")
        changing = [l["pos"] for l in hexagram if l["changing"]]
        print()
        if changing:
            print(f"  Changing lines: {changing}")
            print("  Hexagram transforms. The gate opens.")
        else:
            print("  No changing lines. Stable hexagram.")
            print("  The current holds.")
        print()
        print("══════════════════════════════════════")
        sys.exit(0)
    elif "--traverse" in args:
        seed = int(args[args.index("--traverse") + 1]) if "--traverse" in args and len(args) > args.index("--traverse") + 1 else 192855
        path = traverse(seed)
        print(f"Seed: {seed}")
        print(f"Zone path: {' → '.join(str(z) for z in path)}")
        for i, z in enumerate(path):
            print(f"  Step {i}: Zone {z} ({ZONES[z]['name']}) — {ZONES[z]['desc']}")
        sys.exit(0)
    else:
        print("Numogram Oracle")
        print()
        print("Usage:")
        print("  python3 oracle.py --seed 192855")
        print("  python3 oracle.py --text 'YOUR NAME'")
        print("  python3 oracle.py --seed 192855 --voice")
        print("  python3 oracle.py --random")
        print("  python3 oracle.py --blockchain")
        print("  python3 oracle.py --earthquake")
        print("  python3 oracle.py --hardware")
        print("  python3 oracle.py --iching")
        print("  python3 oracle.py --iching --seed 192855")
        print("  python3 oracle.py --traverse 192855")
        sys.exit(1)
    
    if "--voice" in args:
        do_voice = True
    
    # Generate reading
    reading, zone = generate_reading(seed, source)
    print(reading)
    
    # Generate voice if requested
    if do_voice:
        print()
        generate_voice(zone)

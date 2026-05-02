"""
Scanner — walks watch roots, yields candidate artifacts.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict

# Watch roots: directories where generated artifacts appear
WATCH_ROOTS = [
    os.path.expanduser('~/numogram-tsubuyaki'),
    os.path.expanduser('~/numogram-dreaming.html'),
    os.path.expanduser('~/numogram-labyrinth-webgl.html'),
    os.path.expanduser('~/cult-garden-v2.html'),
    os.path.expanduser('~/cult-garden-v3.html'),
    os.path.expanduser('~/cult-garden-zone-skins.html'),
    os.path.expanduser('~/numogram-zone-wallpapers.py'),
    os.path.expanduser('~/numogame'),
    os.path.expanduser('~/numogram-voices'),
    os.path.expanduser('~/diagram'),
]

# File extensions we consider artifacts
ARTIFACT_EXTS = {'.html', '.svg', '.py', '.json', '.wav', '.mp3', '.md'}

# Exclude these directories
EXCLUDE_DIRS = {'node_modules', '__pycache__', '.git', 'checkpoints', 'build', 'dist', '.venv', 'venv', '.hermes'}

def scan_artifacts(since_hours: int = 24) -> List[Dict]:
    """
    Walk watch roots, return list of candidate artifacts modified in the last `since_hours`.
    Each candidate: {path, rel_path, size, mtime, suggested_name}
    """
    candidates = []
    cutoff = datetime.now().timestamp() - (since_hours * 3600)
    
    for root in WATCH_ROOTS:
        if not os.path.exists(root):
            continue
        if os.path.isfile(root):
            # Single file case
            try:
                mtime = os.path.getmtime(root)
                if mtime > cutoff:
                    candidates.append({
                        'path': root,
                        'rel_path': os.path.relpath(root, os.path.expanduser('~')),
                        'size': os.path.getsize(root),
                        'mtime': mtime,
                        'suggested_name': os.path.basename(root),
                    })
            except:
                pass
            continue
        
        # Directory walk
        for dirpath, dirs, files in os.walk(root):
            # Prune exclude dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
            for fname in files:
                if not any(fname.endswith(ext) for ext in ARTIFACT_EXTS):
                    continue
                if fname.startswith('.'):
                    continue
                full = os.path.join(dirpath, fname)
                try:
                    mtime = os.path.getmtime(full)
                    if mtime > cutoff:
                        candidates.append({
                            'path': full,
                            'rel_path': os.path.relpath(full, os.path.expanduser('~')),
                            'size': os.path.getsize(full),
                            'mtime': mtime,
                            'suggested_name': fname,
                        })
                except:
                    pass
    
    return candidates

if __name__ == '__main__':
    # Quick manual test
    results = scan_artifacts(since_hours=24*7)  # last week
    print(f"Found {len(results)} candidates (last 7d)")
    for c in sorted(results, key=lambda x: x['mtime'], reverse=True)[:10]:
        age_h = (datetime.now().timestamp() - c['mtime']) / 3600
        print(f"  +{age_h:.1f}h  {c['rel_path']}  ({c['size']//1024}KB)")

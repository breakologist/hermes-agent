"""
Migrator — copies artifact candidates into wiki/assets/
"""

import os
import shutil
import hashlib

ASSETS_DIR = '/home/etym/.hermes/obsidian/hermetic/wiki/assets'

def migrate_artifact(candidate: dict, dry_run: bool = True) -> dict:
    """
    Copy `candidate['path']` → ASSETS_DIR/ with name deduplication.
    Returns migration record {src, dst, sha256, action}.
    """
    src = candidate['path']
    base_name = candidate['suggested_name']
    dst = os.path.join(ASSETS_DIR, base_name)
    
    # If exists, add numeric suffix
    if os.path.exists(dst):
        name, ext = os.path.splitext(base_name)
        counter = 1
        while os.path.exists(dst):
            dst = os.path.join(ASSETS_DIR, f"{name}__{counter}{ext}")
            counter += 1
    
    record = {'src': src, 'dst': dst, 'sha256': None, 'action': 'copy' if dry_run else 'copied'}
    
    if dry_run:
        return record
    
    # Actual copy
    shutil.copy2(src, dst)
    # Hash
    h = hashlib.sha256()
    with open(dst, 'rb') as fh:
        while chunk := fh.read(8192):
            h.update(chunk)
    record['sha256'] = h.hexdigest()
    return record

if __name__ == '__main__':
    # Demo
    from scanner import scan_artifacts
    candidates = scan_artifacts(since_hours=24*30)
    if candidates:
        result = migrate_artifact(candidates[0], dry_run=True)
        print(f"Would migrate: {result}")

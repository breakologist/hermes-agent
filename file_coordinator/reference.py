"""
Reference Updater — rewrites tilde-path wiki links to assets/ relative links.
"""

import os
import re

WIKI_DIR = '/home/etym/.hermes/obsidian/hermetic/wiki'

def find_tilde_references(page_content: str):
    """Yield (match_object, expanded_path) for each ~/… reference."""
    pattern = re.compile(r'~/([^\s\[\]\n]+)')
    for m in pattern.finditer(page_content):
        target = os.path.expanduser(m.group(0))
        yield m, target

def fix_tilde_references(page_name: str, migrated_assets: list, dry_run: bool = True):
    """
    For a given wiki page, replace tilde refs that point to files in `migrated_assets`
    (list of absolute source paths) with relative `assets/filename` links.
    Returns list of replacements made.
    """
    page_path = os.path.join(WIKI_DIR, page_name)
    with open(page_path) as fh:
        content = fh.read()
    
    replacements = []
    for m, target_path in find_tilde_references(content):
        if target_path in migrated_assets:
            filename = os.path.basename(target_path)
            new_ref = f'[[assets/{filename}]]'
            replacements.append({
                'old': m.group(0),
                'new': new_ref,
                'line': content[:m.start()].count('\n') + 1,
            })
            if not dry_run:
                content = content.replace(m.group(0), new_ref, 1)
    
    if replacements and not dry_run:
        with open(page_path, 'w') as fh:
            fh.write(content)
    
    return replacements

if __name__ == '__main__':
    print("reference.py stub — call fix_tilde_references(page_name, migrated_assets, dry_run=False)")

"""
Audit logger — records all coordination actions to log.md
"""

import os
from datetime import datetime

HERMES_LOG = os.path.expanduser('~/.hermes/log.md')

def log_migration(action: str, details: dict):
    """
    Append a structured entry to the Hermes log.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"## [{timestamp}] file-coord | {action}\n"
    for k, v in details.items():
        entry += f"  {k}: {v}\n"
    entry += "\n"
    
    # Append
    with open(HERMES_LOG, 'a') as fh:
        fh.write(entry)

if __name__ == '__main__':
    log_migration('test', {'msg': 'audit stub works'})
    print("Wrote test entry to", HERMES_LOG)

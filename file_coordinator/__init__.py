"""
file_coordinator — Cross-cutting file system coordination for Hermes.

Phase 0 (April 2026): Design doc in workspace/FILE-COORDINATION.md
Phase 1 (now): Stub API, scanner skeleton
Phase 2: Migration logic
Phase 3: evey-goals + cron integration
"""

from .scanner import scan_artifacts
from .migrator import migrate_artifact
from .reference import fix_tilde_references
from .exporter import sync_vault_export
from .audit import log_migration

__all__ = ['scan_artifacts', 'migrate_artifact', 'fix_tilde_references', 'sync_vault_export', 'log_migration']
__version__ = '0.1.0'

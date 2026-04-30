"""Tests for the curator consolidated-vs-pruned classifier.

The classifier splits skills that disappeared between the before/after
snapshots into two buckets:

- "consolidated" — absorbed into an umbrella; content still lives
  under another skill's files
- "pruned" — archived for staleness; content not preserved elsewhere

Without the split the report lumped everything under "Skills archived",
which misled users into thinking consolidated skills had been pruned.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture
def curator_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "skills").mkdir()
    (home / "logs").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    import importlib
    import hermes_constants
    importlib.reload(hermes_constants)
    from agent import curator
    importlib.reload(curator)
    yield curator


def test_classify_consolidated_via_write_file_evidence(curator_env):
    """skill_manage write_file on umbrella references/<removed>.md = consolidated."""
    result = curator_env._classify_removed_skills(
        removed=["axolotl-training"],
        added=[],
        after_names={"training-platforms", "keeper"},
        tool_calls=[
            {
                "name": "skill_manage",
                "arguments": json.dumps({
                    "action": "write_file",
                    "name": "training-platforms",
                    "file_path": "references/axolotl-training.md",
                    "file_content": "# Axolotl\n...",
                }),
            },
        ],
    )
    assert len(result["consolidated"]) == 1
    assert result["consolidated"][0]["name"] == "axolotl-training"
    assert result["consolidated"][0]["into"] == "training-platforms"
    assert result["pruned"] == []


def test_classify_pruned_when_no_destination_reference(curator_env):
    """Removed skill with no referencing tool call = pruned."""
    result = curator_env._classify_removed_skills(
        removed=["old-stale-thing"],
        added=[],
        after_names={"keeper"},
        tool_calls=[
            {"name": "skills_list", "arguments": "{}"},
            {"name": "skill_manage", "arguments": json.dumps({
                "action": "patch", "name": "keeper",
                "old_string": "foo", "new_string": "bar",
            })},
        ],
    )
    assert result["consolidated"] == []
    assert len(result["pruned"]) == 1
    assert result["pruned"][0]["name"] == "old-stale-thing"


def test_classify_consolidated_into_newly_created_umbrella(curator_env):
    """Removed skill absorbed into a skill that was created THIS run."""
    result = curator_env._classify_removed_skills(
        removed=["anthropic-api"],
        added=["llm-providers"],  # new umbrella
        after_names={"llm-providers"},
        tool_calls=[
            {
                "name": "skill_manage",
                "arguments": json.dumps({
                    "action": "create",
                    "name": "llm-providers",
                    "content": "# LLM Providers\n\n## anthropic-api\nMerged from the old anthropic-api skill.\n",
                }),
            },
        ],
    )
    assert len(result["consolidated"]) == 1
    assert result["consolidated"][0]["name"] == "anthropic-api"
    assert result["consolidated"][0]["into"] == "llm-providers"


def test_classify_handles_underscore_hyphen_variants(curator_env):
    """Names with hyphens match underscore forms in paths/content and vice versa."""
    result = curator_env._classify_removed_skills(
        removed=["open-webui-setup"],
        added=[],
        after_names={"webui"},
        tool_calls=[
            {
                "name": "skill_manage",
                "arguments": json.dumps({
                    "action": "write_file",
                    "name": "webui",
                    "file_path": "references/open_webui_setup.md",
                    "file_content": "...",
                }),
            },
        ],
    )
    assert len(result["consolidated"]) == 1
    assert result["consolidated"][0]["into"] == "webui"


def test_classify_self_reference_does_not_count(curator_env):
    """A tool call that targets the removed skill itself is NOT consolidation."""
    # e.g. the curator patched the skill once and later archived it
    result = curator_env._classify_removed_skills(
        removed=["doomed"],
        added=[],
        after_names={"keeper"},
        tool_calls=[
            {
                "name": "skill_manage",
                "arguments": json.dumps({
                    "action": "patch",
                    "name": "doomed",  # same as removed
                    "old_string": "x",
                    "new_string": "y",
                }),
            },
        ],
    )
    assert result["consolidated"] == []
    assert result["pruned"][0]["name"] == "doomed"


def test_classify_destination_must_exist_after_run(curator_env):
    """A reference to a skill that doesn't exist after the run can't be the umbrella."""
    result = curator_env._classify_removed_skills(
        removed=["thing"],
        added=[],
        after_names={"keeper"},  # "ghost" not in here
        tool_calls=[
            {
                "name": "skill_manage",
                "arguments": json.dumps({
                    "action": "write_file",
                    "name": "ghost",  # not in after_names
                    "file_path": "references/thing.md",
                    "file_content": "...",
                }),
            },
        ],
    )
    assert result["consolidated"] == []
    assert result["pruned"][0]["name"] == "thing"


def test_classify_mixed_run_produces_both_buckets(curator_env):
    """A realistic run: one skill consolidated, one skill pruned."""
    result = curator_env._classify_removed_skills(
        removed=["absorbed-skill", "dead-skill"],
        added=["umbrella"],
        after_names={"umbrella", "keeper"},
        tool_calls=[
            {
                "name": "skill_manage",
                "arguments": json.dumps({
                    "action": "write_file",
                    "name": "umbrella",
                    "file_path": "references/absorbed-skill.md",
                    "file_content": "...",
                }),
            },
        ],
    )
    assert len(result["consolidated"]) == 1
    assert result["consolidated"][0]["name"] == "absorbed-skill"
    assert result["consolidated"][0]["into"] == "umbrella"
    assert len(result["pruned"]) == 1
    assert result["pruned"][0]["name"] == "dead-skill"


def test_classify_handles_malformed_arguments_string(curator_env):
    """Truncated/malformed JSON in arguments falls back to substring match."""
    # Arguments truncated to 400 chars may not parse as JSON.
    truncated_raw = (
        '{"action":"write_file","name":"umbrella","file_path":"references/'
        'absorbed-skill.md","file_content":"long content that was cut off mid'
    )
    result = curator_env._classify_removed_skills(
        removed=["absorbed-skill"],
        added=[],
        after_names={"umbrella"},
        tool_calls=[
            {"name": "skill_manage", "arguments": truncated_raw},
        ],
    )
    # Fallback substring match finds "absorbed-skill" in the raw truncated string
    # even though json.loads fails — but it can't identify target="umbrella"
    # because _raw is the only haystack and there's no dict access. The
    # classifier only promotes to "consolidated" if it can identify a target
    # skill from args.get("name"). Ensure we fail safe: no false positive.
    # (This is a correctness floor — better to prune-label than hallucinate
    # an umbrella that wasn't really used.)
    assert result["consolidated"] == []
    assert len(result["pruned"]) == 1


def test_report_md_splits_consolidated_and_pruned_sections(curator_env):
    """End-to-end: REPORT.md shows both sections distinctly."""
    curator = curator_env
    start = datetime.now(timezone.utc)

    before = [
        {"name": "absorbed-skill", "state": "active", "pinned": False},
        {"name": "dead-skill", "state": "stale", "pinned": False},
        {"name": "keeper", "state": "active", "pinned": False},
    ]
    after = [
        {"name": "keeper", "state": "active", "pinned": False},
        {"name": "umbrella", "state": "active", "pinned": False},
    ]

    run_dir = curator._write_run_report(
        started_at=start,
        elapsed_seconds=60.0,
        auto_counts={"checked": 3, "marked_stale": 0, "archived": 0, "reactivated": 0},
        auto_summary="no auto changes",
        before_report=before,
        before_names={r["name"] for r in before},
        after_report=after,
        llm_meta={
            "final": "Consolidated absorbed-skill into umbrella. Pruned dead-skill.",
            "summary": "1 consolidated, 1 pruned",
            "model": "m",
            "provider": "p",
            "error": None,
            "tool_calls": [
                {
                    "name": "skill_manage",
                    "arguments": json.dumps({
                        "action": "create",
                        "name": "umbrella",
                        "content": "# umbrella\n\nAbsorbed absorbed-skill.",
                    }),
                },
            ],
        },
    )

    payload = json.loads((run_dir / "run.json").read_text())
    # Both lists exist and are disjoint
    consolidated_names = {e["name"] for e in payload["consolidated"]}
    assert consolidated_names == {"absorbed-skill"}
    assert payload["pruned"] == ["dead-skill"]
    # The union still matches the legacy "archived" field for backward compat
    assert set(payload["archived"]) == consolidated_names | set(payload["pruned"])
    # counts exposed
    assert payload["counts"]["consolidated_this_run"] == 1
    assert payload["counts"]["pruned_this_run"] == 1

    md = (run_dir / "REPORT.md").read_text()
    # Two separate sections, not a single "Skills archived" lump
    assert "Consolidated into umbrella skills" in md
    assert "Pruned — archived for staleness" in md
    assert "`absorbed-skill` → merged into `umbrella`" in md
    assert "`dead-skill`" in md
    # The old single-lump section should not appear
    assert "### Skills archived" not in md

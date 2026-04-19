---
name: hermes-agent-swap
description: Safely swap or upgrade hermes-agent installations (e.g., switching to a fork like outsourc-e/hermes-agent). Includes pre-flight verification, safe swap procedure, and post-swap validation.
triggers:
  - swap hermes-agent
  - upgrade hermes-agent
  - switch to hermes-agent fork
  - replace hermes-agent
---

# Hermes Agent Swap

## Critical Pitfall
**NEVER move or delete the hermes-agent directory while the gateway is running.** The gateway process holds file handles to the Python venv and all source files. Moving the directory causes `FileNotFoundError` on every API call until the gateway is fully restarted. If this happens, the only fix is to restore the directory and restart the gateway.

## Pre-flight: Verify Current State

```bash
# Check gateway is running and which repo it's from
cd ~/.hermes/hermes-agent && git remote -v && git log --oneline -1

# Check what's listening
ss -tlnp | grep 8642

# Back up config
cp ~/.hermes/.env /tmp/hermes-env-backup
cp ~/.hermes/config.yaml /tmp/hermes-config-backup
```

## Safe Swap Procedure

### Step 1: Stop the gateway FIRST
```bash
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway stop
sleep 2
ss -tlnp | grep 8642 || echo "Gateway stopped"
```

### Step 2: Clone the new version to a temp directory

**VERIFY THE FORK EXISTS FIRST.** If the clone fails, you'll be left with no agent.

```bash
# Test the URL before committing
git ls-remote https://github.com/<fork>/hermes-agent.git HEAD 2>&1 | head -1
# If this fails, DO NOT proceed with the swap

git clone https://github.com/<fork>/hermes-agent.git /tmp/hermes-agent-new
cd /tmp/hermes-agent-new
```

If the clone fails after stopping the gateway, restore immediately:
```bash
# Don't panic — the backup is still at ~/.hermes/hermes-agent-backup-*
mv ~/.hermes/hermes-agent-backup-* ~/.hermes/hermes-agent
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace
```

### Step 3: Only after confirming temp clone exists, swap directories
```bash
mv ~/.hermes/hermes-agent ~/.hermes/hermes-agent-backup-$(date +%Y%m%d)
mv /tmp/hermes-agent-new ~/.hermes/hermes-agent
```

### Step 4: Restore config and install deps
```bash
cp /tmp/hermes-env-backup ~/.hermes/.env
cp /tmp/hermes-config-backup ~/.hermes/config.yaml
cd ~/.hermes/hermes-agent
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Step 5: Restart gateway
```bash
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace
```

## Post-swap Verification

```bash
# Gateway should be listening
ss -tlnp | grep 8642

# Check the new remote
cd ~/.hermes/hermes-agent && git remote -v

# Verify API works
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8642
```

## Config Verification (Hermes Workspace)

When hermes-workspace is running alongside the gateway, verify config alignment:

1. **config.yaml** — check `model.default`, `provider`, `base_url`:
   ```bash
   python3 -c "import yaml; c=yaml.safe_load(open('/home/etym/.hermes/config.yaml')); m=c['model']; print(f'provider: {m[\"provider\"]}'); print(f'model: {m[\"default\"]}'); print(f'base_url: {m[\"base_url\"]}')"
   ```

2. **Auth store** — verify OAuth tokens exist for the provider:
   ```bash
   python3 -c "import json; a=json.load(open('/home/etym/.hermes/auth.json')); print('Providers:', list(a['providers'].keys()))"
   ```

3. **Model metadata** — confirm context window from hermes-agent:
   ```bash
   grep -i '<model-name>' ~/.hermes/hermes-agent/agent/model_metadata.py
   ```

## Fork-Specific Notes

- **outsourc-e/hermes-agent**: Enhanced fork with extra API endpoints (sessions, memory, skills, config). Required for full hermes-workspace features. Without it, workspace runs in "portable mode" (basic chat only).
- **NousResearch/hermes-agent**: Vanilla/official. Portable mode only with workspace.

---
name: search-fallback
description: Search fallback chain — when web_research fails, what to try next. Documents priority order, known failure modes, and workarounds for environments where SearXNG or DuckDuckGo are unavailable.
version: 1.1.0
tools:
  - web_research
  - web_extract
  - browser_navigate
  - terminal
---

# Search Fallback Chain

When `web_research` fails with `SEARXNG_URL not configured`, follow this priority chain.

## Priority Order

```
1. web_research / web_search    → Needs SearXNG running or paid API key
2. ddgs CLI                     → Free, no API key, but blocked on cloud IPs
3. web_extract on known URLs    → Always works, but you need the URL first
4. browser_navigate to Google   → Heavyweight last resort
```

## Step 1: Try web_research first

Always try `web_research` first. If it returns `SEARXNG_URL not configured`, SearXNG is not running. Go to Step 2.

## Step 2: DuckDuckGo via `ddgs` CLI

```bash
command -v ddgs && ddgs text -k "your query" -m 5
```

**Cloud/VPS pitfall:** DuckDuckGo blocks non-residential IPs. The CLI returns `AttributeError: 'NoneType' object has no attribute 'replace'` — this is a hard block, not a transient error. Don't retry, go to Step 3.

**Residential IPs:** Works fine. Install with `pipx install ddgs`.

## Step 3: web_extract on known URLs

If you know the URL (or can construct it from patterns like `https://github.com/org/repo/releases`), use `web_extract` directly. No search engine needed.

```bash
# Example: GitHub releases
web_extract(url="https://github.com/NousResearch/hermes-agent/releases", max_chars=10000)

# Example: Blog post if you know the slug
web_extract(url="https://example.com/blog/2026/04/post-title", max_chars=5000)
```

**Pattern-based URL construction:** Many sites have predictable URL structures:
- GitHub releases: `https://github.com/{owner}/{repo}/releases`
- GitHub tags: `https://github.com/{owner}/{repo}/releases/tag/{tag}`
- Wikipedia: `https://en.wikipedia.org/wiki/{topic}`
- PyPI: `https://pypi.org/project/{package}/`
- Docs: `https://{project}.readthedocs.io/en/latest/`

## Step 4: Browser search (last resort)

Use `browser_navigate` to a search engine when nothing else works:

```
browser_navigate(url="https://www.google.com/search?q=your+query")
browser_snapshot()  # Read results
browser_click(ref="@N")  # Click a result
```

**Camofox (Node.js server):** Hermes has built-in Camofox browser tools at `~/.hermes/tools/browser_camofox.py`. This is a Node.js server wrapping Camoufox (anti-detection Firefox) with a REST API — different from standalone Camoufox. Activate with:
- `docker run -p 9377:9377 -e CAMOFOX_PORT=9377 jo-inc/camofox-browser` (or npm from https://github.com/jo-inc/camofox-browser)
- Set `CAMOFOX_URL=http://localhost:9377` in `~/.hermes/.env`

Browser tools then route through it automatically — anti-detection fingerprinting, persistent profiles, etc. Useful for sites that block headless browsers.

Slow but always works regardless of IP restrictions.

## Permanent Fix: Set Up SearXNG

If you do frequent searching, spin up a SearXNG container with persistent config:

```bash
# Create config directory
mkdir -p ~/.hermes/searxng

# Write settings (generates secret key, enables JSON format, no limiter)
SECRET=$(openssl rand -hex 32)
cat > ~/.hermes/searxng/settings.yml << EOF
use_default_settings: true
server:
  bind_address: "0.0.0.0"
  secret_key: "$SECRET"
  limiter: false
  image_proxy: true
search:
  safe_search: 0
  default_lang: "en"
  formats:
    - html
    - json
engines:
  - name: google
    disabled: false
  - name: bing
    disabled: false
  - name: duckduckgo
    disabled: false
  - name: wikipedia
    disabled: false
  - name: brave
    disabled: false
EOF

# Run with config volume mount and auto-restart
docker run -d \
  --name hermes-searxng \
  --restart unless-stopped \
  -p 8888:8080 \
  -v ~/.hermes/searxng:/etc/searxng \
  searxng/searxng
```

**Pitfall: bare `docker run` without config mount.** The default config has `limiter: true` which can reject requests, and no `secret_key` which causes warnings. Always mount a custom settings.yml.

**Pitfall: Config file permissions after container runs.** The SearXNG container rewrites settings.yml with its own user. After first run, you can't edit it directly (sed/tee get permission denied). Use `docker cp` instead:
```bash
docker cp hermes-searxng:/etc/searxng/settings.yml /tmp/searxng.yml
# edit /tmp/searxng.yml
docker cp /tmp/searxng.yml hermes-searxng:/etc/searxng/settings.yml
docker restart hermes-searxng
```

**Env vars — set BOTH** (different plugins use different names):
```bash
# Add to ~/.hermes/.env
SEARXNG_URL=http://localhost:8888
SEARXNG_INSTANCE_URL=http://localhost:8888
```

- `evey-research` plugin checks `SEARXNG_URL`
- `web-search-plus` plugin checks `SEARXNG_INSTANCE_URL`
- `evey-news` plugin checks `SEARXNG_URL`

**Restart required:** Plugins read env at load time. Changes to `.env` won't take effect until hermes-agent restarts. If testing immediately, verify with curl:
```bash
curl -s "http://localhost:8888/search?q=test&format=json" | head -c 200
```

**Alternative: Paid APIs** (if SearXNG isn't viable):
- Serper: 2,500 free/month at serper.dev — set `SERPER_API_KEY`
- Tavily: 1,000 free/month at tavily.com — set `TAVILY_API_KEY`

## Failure Mode Reference

| Symptom | Cause | Action |
|---------|-------|--------|
| `SEARXNG_URL not configured` | No SearXNG running | Skip to Step 2 |
| `AttributeError: 'NoneType' ... replace` from ddgs | DuckDuckGo blocked cloud IP | Skip to Step 3 |
| `ModuleNotFoundError: No module named 'ddgs'` | execute_code sandbox is separate from terminal | Use terminal + ddgs CLI instead |
| web_extract returns HTML junk | Page requires JS rendering | Use browser_navigate instead |
| web_extract 404 | URL is wrong or changed | Try Google cache or browser |

## Tips

- web_extract is underrated — if you can guess or construct the URL, it's faster than search
- GitHub repos always have `/releases`, `/issues`, `/wiki` paths — try before searching
- For code/library questions, direct PyPI/npm docs pages are faster than generic search
- Keep SearXNG running on machines that search frequently — the setup cost is one docker command

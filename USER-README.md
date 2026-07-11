So what now?  Going forward, how do I use this?  Where is my list? and after downloading, how do I tell future instances of an LLM agent to use the downloaded things?

Three answers, all concrete.

Where the list is. The page itself is reports/catalog/index.html in the repo — all 7,479 rows, filterable by status, marketplace, and category. Two ways to open it: run bash progress/serve.sh in the repo and visit http://localhost:8787/catalog.html, or just double-click the HTML file — it's self-contained. CATALOG.md is the plain-markdown fallback that GitHub renders directly if you're browsing on the web. The actual files behind the verified rows live in vault/<id>/<version>/ on your machine (gitignored — the repo carries the proofs, your disk carries the goods), described by the 2,145 manifests and the two databases (corpus.db = facts, corpus_kb.db = search).

How you use it, day to day. Browse the catalog page when you want to shop by eye. Green ✓ rows are already in your vault. click_to_get rows are the checkout-gated ones: click the link, complete the $0 checkout with the project account, then drop the downloaded file into inputs/dropzone/ — the next agent session probes it, promotes the row to verified, mints its card, and it becomes searchable like everything else. When you want to find rather than browse, ask any Claude Code session opened in that repo in plain English — "find me something that makes frost spread across glass" — and it uses the search layer. Maintenance needs nothing from you: discovery runs monthly, re-verification quarterly; your only calendar item is the token renewal GitHub will email about in October.

How future LLM instances use it — the question the whole navigation layer was built to answer. If the session is opened inside the repo, you say nothing at all: CLAUDE.md auto-loads, the blender-vault-corpus MCP server is registered, and CORPUS.md teaches the agent the interface in under 2k tokens. For any other project — the Stage 2 engine repo, a random experiment, even a non-Claude model (everything is SQLite and plain Python by design) — you paste this once into its instructions or CLAUDE.md:

TOOL LIBRARY: the Blender Vault corpus lives at ~/dev/blender-engine (read-only dependency).
1. Read its CORPUS.md FIRST — that file is the interface; follow it over your assumptions.
2. Find capabilities via the blender-vault-corpus MCP server, or:
   uv run .archon/scripts/corpus_cli.py  (search_capabilities for natural-language needs,
   query_registry for exact verb/medium/quality facets, get_card + get_usage before use).
3. IRON RULES: retrieval proposes, the registry disposes — only invoke entries the registry
   confirms verified; recipe_unverified and graveyard entries are never invocable. Every
   render must emit the attribution string from each used entry's meta.json, must never
   3D-export scenes containing BlenderKit assets, and must respect HANDOFF.md §5 licenses.
4. The actual files are in vault/<id>/<version>/ — install or append per the entry's card.
(Adjust the path to wherever the repo lives on your machine.) That block plus the repo is the entire handoff — a fresh instance with zero context passed exactly this test at eval time: found real tools by meaning, refused the gaps, caught the license traps.

And that's also the answer to "what now": whenever you're ready to build Diegesis itself, the Stage 2 conversation opens with that snippet as its first given. The library stopped being the project the moment you committed D-009 — now it's the shelf the next project reaches for.
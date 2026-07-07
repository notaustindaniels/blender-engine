# Marketplace / A-lane ToS-check pass (D-003 R20 + D-004 R28) — 2026-07-07

Findings from a live ToS read, posted BEFORE any acquisition batch (owner's build order). Automation
posture per source. **When a ToS is unread or ambiguous, the default is fully human-gated** — never
assume permission. No guardrail loosening (D-003 R20).

## L5a — Gumroad
- **Finding (verbatim, ToS §14 "User Conduct"):** prohibits use of *"any manual or automated software,
  devices or other processes (including but not limited to spiders, robots, scrapers, crawlers,
  avatars, data mining tools or the like) to 'scrape' or download data from any web pages"* and
  anything that *"bypasses our robot exclusion hardware"*.
- **No clause** restricts a buyer downloading products they have legitimately obtained; assisted/
  human-in-the-loop $0 checkout is **not addressed** (neither permitted nor forbidden explicitly).
- **POSTURE → NO automated marketplace scraping.** Automated Playwright discovery of Gumroad listings
  would violate §14 (this is stricter than SPEC §5.4 assumed — recorded as a §12.5 amendment).
  Acquisition is **fully human-gated**: the human browses, completes the $0 checkout, and downloads
  from their own library. Mirror-checking is done via **web search** ("<product> blender github"),
  NOT by scraping Gumroad pages. GitHub-mirror reroute BEFORE any checkout (SPEC §5.4).

## L5b — Superhive (formerly Blender Market)
- **ToS DISCHARGED 2026-07-07 by the owner's advisor** (search retrieval got past the WAF that
  blocked the agent's direct fetch). Sources: `superhivemarket.com/policies/terms-of-service` and
  `support.superhivemarket.com/article/42-terms-of-use-site`.
- **Findings (from retrieved sections):** **No explicit anti-scraping clause** in the retrieved text
  (unlike Gumroad §14). BUT: membership with *"accurate, current, and complete"* information is required
  to purchase; purchases are per-product **LICENSES** (GPL / CC-BY / royalty-free vary by product —
  **capture per item, R26**); **all transactions must run through their checkout**; termination is at
  their sole discretion.
- **POSTURE → conservative, identical to Gumroad:** no automated marketplace scraping (the WAF is
  itself a signal), search-derived product URLs only, **human checkout only**. Runs last (SPEC order).
- **Honesty caveat:** full ToS text was WAF-blocked to the agent; this posture is set from the
  advisor-retrieved sections, not a complete verbatim read.

## A1 — Sketchfab (asset lane, D-004)
- **Finding:** official **Download API** for 700k+ CC-licensed models. Requires OAuth2 Bearer token;
  app must **clearly display the model's CC license + author attribution + "provided by Sketchfab"**;
  attribution must follow the asset everywhere. Models delivered as glTF/GLB/USDZ (not source FBX/OBJ).
- **POSTURE → API-automatable for CC content**, gated on `SKETCHFAB_TOKEN` (`.archon/.env`, never in
  chat/YAML — R28). Capture `usage_license` + attribution per item (R26). This is a legitimate,
  ToS-blessed automated path — no scraping, no checkout. Awaiting owner-created account + token.

## A2 — ArtStation · A3 — Fab (asset lanes, D-004)
- **POSTURE → ToS-check pass DEFERRED to activation (R29): A2/A3 begin only after the first L5a
  approval batch ships.** Their ToS will be read (and posted here) before any discovery automation.
  Anything checkout-shaped stays human-gated exactly like L5. Fab is A3 (supersedes the earlier "L5c").

## Cross-cutting rules (all lanes)
- **License is load-bearing (R26):** engine-locked licenses and `.uasset`-only downloads → graveyard.
  NC/ND → acquired but segregated pending an owner call. cc-by attribution recorded per item.
- **No paid acquisition ever** without an owner D-entry (R23). $0 / PWYW-$0 only, legitimately.
- **Never nulled/pirated** — a $0 obtained illegitimately is a hard fail (PRD guardrail #3).

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
- **Finding:** ToS page (`superhivemarket.com/policies/terms-of-service`) is **WAF-blocked (HTTP 403)**
  to automated fetch — **UNREAD by the agent.** Known: membership is free; licenses are per-product and
  explicitly the buyer's responsibility to understand; operated by Autotroph, Inc.
- **POSTURE → fully human-gated + FLAG.** The anti-automation clause could not be read; default to the
  safest posture (human discovery + human $0 checkout). **Owner action needed: a manual ToS read**
  before any L5b automation of any kind. Runs last (SPEC lane order).

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

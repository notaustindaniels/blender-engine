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

## A2 — ArtStation (asset lane, D-004) — **DROPPED (R32a), 2026-07-07**
- **Finding (ToS read):** ArtStation ToS states *"Users may only access the Services through the
  interface provided on the Site"* and prohibits collecting/mining/scraping content; **no official
  public download API**. Source: artstation.com/tos.
- **DISPOSITION → DROP the automated A2 lane (R32a: a ToS that forbids the plan drops the lane with a
  recorded finding, no escalation).** Site-interface-only access + no API forecloses automated CC
  discovery/download. (A human could still manually download a specific CC asset, but that is not an
  automatable lane and is not pursued.)

## A3 — Fab (asset lane, D-004) — **DROPPED (automated lane) (R32a), 2026-07-07**
- **Finding (ToS read):** Fab offers CC + Standard licenses; access is via the **website (human),
  Fab launcher, or UE/UEFN engine integration**. **No automatable public CC-download API**; the
  engine-integration path yields **`.uasset`** (engine-locked → graveyard per R26). Source:
  fab.com/terms-of-service, fab.com/eula.
- **DISPOSITION → DROP the automated A3 lane (R32a).** No clean automatable CC path; engine-locked
  formats are useless to us. Human website download of a specific CC asset remains possible but is
  not an automatable lane. A1 Sketchfab is the one working automatable asset lane.

## Cross-cutting rules (all lanes)
- **License is load-bearing (R26):** engine-locked licenses and `.uasset`-only downloads → graveyard.
  NC/ND → acquired but segregated pending an owner call. cc-by attribution recorded per item.
- **No paid acquisition ever** without an owner D-entry (R23). $0 / PWYW-$0 only, legitimately.
- **Never nulled/pirated** — a $0 obtained illegitimately is a hard fail (PRD guardrail #3).

## L6 — BlenderKit (D-001 R10 backlog activated under R37 no-spend, 2026-07-07) — **ACTIVATED with constraint**
- **Finding (ToS read, blenderkit.com/terms-and-conditions-2021):** assets are **CC0** or **Royalty-Free**
  (per-asset, creator's choice — capture per item, R26). Use in other software IS permitted: *"You can
  also use the products to create computer games and other computer programs, virtual reality,
  simulations, web or mobile applications or to create other software."*
- **BINDING Article-5 constraint (rides into Stage-2):** *"The product must be used in the project in
  such a format that it cannot be opened or separated by a third party… the software may not contain any
  functionality that would allow end users to export any 3D model from the software."* Our engine outputs
  **rendered video** (not exportable 3D) → **compliant**, but Stage-2 must NOT offer 3D-export of scenes
  containing BlenderKit assets. **Royalty-Free** additionally: incorporation-only, no standalone
  redistribution. Recorded as a per-asset usage constraint (R26).
- **Automation:** no anti-bot/bulk-download clause found; official API + add-on exist (legitimate access).
- **POSTURE → ACTIVATE (not dropped).** HYBRID (owner): node-groups + materials = procedural → standard
  Gate (materials via the shader-probe, gate-eligible); models = assets → A-lane ledger (never coverage).
  Blocked on `BLENDERKIT_API_KEY` (env-only, R2). If the key/API later proves to forbid bulk access, drop
  with a finding. Per-asset license (cc0/royalty-free) + the Article-5 constraint captured on every item.

## itch.io — new lattice vein (D-009 R58, 2026-07-10) — **JOINS via official RSS (discovery only)**
- **Finding (ToS read, `itch.io/docs/legal/terms` + `itch.io/docs/api/overview`):** the ToS excerpt read
  contains **no explicit anti-scraping / robot-exclusion clause** (unlike Gumroad §14). There is **no
  public catalog/download API** for third-party enumeration — the server-side API manages *your own*
  account, OAuth acts *on behalf of a user*, and the JS API is an embedded buy-button. **BUT itch.io
  documents official RSS feeds as its public discovery mechanism:** any browse-page URL + `.xml` yields a
  feed (new uploads, featured, sales, and tag/category browse pages).
- **POSTURE → JOIN the standing lattice as an RSS-fed discovery vein.** Consume ONLY the official RSS
  feeds (a published, machine-readable format explicitly provided for programmatic consumption — this is
  not "scraping" and needs no robot-exclusion bypass) + search-derived product URLs. **No HTML scraping**
  of listing pages. **Human checkout only** — itch.io free/PWYW games download after a $0 checkout the
  owner performs (click_to_get rows; never automated, R33). Capture price_class + license confirm-at-source
  per item (R26/R31). Compatible with the external-discovery posture → added to the lattice config.
- **Honesty caveat (same as Superhive):** the ToS excerpt read was **partial** (the full API-terms page
  was not in the fetched excerpt); posture is set conservatively from the documented RSS mechanism + the
  absence of an anti-automation clause in what was read. If a fuller read later surfaces an anti-automation
  clause, drop the vein with a finding (R32a). Same ToS-read-first rule applies to any future vein.

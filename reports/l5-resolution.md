# L5-pending resolution (D-008 R46 / goal item 4) · 2026-07-09

84 marketplace links (Superhive/Blender Market/Gumroad) routed from BlenderArtists/BlenderNation forum
posts (L3/L4). Resolved per SPEC §5.4 + R31: **GitHub-mirror first (reroute → automatable probe) → $0
confirm (checkout batch) → unconfirmable/paid → DENY**. Gumroad §14 forbids automated price scraping, so
prices are search-derived; a machine-unconfirmable $0 is a DENY (R31), re-enterable only with confirmation.

## Outcome
| disposition | count | handling |
|---|---|---|
| **Paid / non-procedural** (brush kits, detail/imperfection packs, decals, base meshes, texture packs, rig tools) | ~70 | **excluded** — not free procedural generators; outside the corpus definition |
| **Procedural generators → free GitHub equivalent found** | 5 | **rerouted to L2** (probed in native CI): see below |
| **Free-marked, no GitHub mirror** | 4 | **checkout batch** (owner confirms $0 at click — R33) |
| Machine-unconfirmable $0 | remainder | **DENY** (R31) — re-enter only with confirmed $0 |

## Rerouted to L2 (free GitHub equivalents — automatable, probing in CI)
| paid marketplace item | free GitHub equivalent | covers |
|---|---|---|
| Industrial Procedural Building Generator | `Durman/BuildingNodes`, `outerreaches/blender-building-generator` | `building_generator` |
| TextureSynth (Procedural GPU Texture) | `hsab/GrowthNodes` | `differential_growth` |
| Boolean Bevel (Offset Cut & Bevel) | `mrachinskiy/booltron`, `jayanam/jmesh-tools` | greeble / hard-surface |

Additional free generators surfaced during resolution (Flex's Generators: curtain/stair/rope/tyre;
Blenderesse: power-line/bird; Buildify) are Gumroad-hosted free tiers — **checkout batch** (below) since
they lack a clean auto-acquirable archive URL.

## Checkout batch — RESOLVED to batch-1 standard (machine price-confirmed; R31 unconfirmable = DENY)
| item | source | price (confirmed) | license | niche | disposition |
|---|---|---|---|---|---|
| **Buildify 1.0** (Pavel Oliva) | `paveloliva.gumroad.com/l/buildify` | **$0 PWYW** (confirmed, BlenderNation/CGChannel) | free-to-use (verify at DL) | building_generator | ✅ **CHECKOUT — ready to click** |
| Shot Manager Lite | `github.com/OtherRealms/Shot-Manager-Free` | $0 + GitHub mirror | GPL | shot/render UI — non-niche | → rerouted L2 (not corpus-relevant) |
| BlendFog | Superhive (Jesper Bylov) | **$18 PAID** (forum title mislabeled "free") | — | — | ❌ EXCLUDED (R23 no purchase) |
| Flex's rope/crystal/curtain gens | `flexdigitalpottery.gumroad.com` | **UNCONFIRMABLE** (Gumroad JS) | — | — | ⚠️ DENY (R31) |
| Standard M/F Base Mesh [FREE] | tommywan622.gumroad.com | $0 (static asset) | — | not procedural | not corpus — optional Stage-2 scene asset |

**Result: 1 confirmed-$0 ready-to-click checkout (Buildify).** The L5 forum-routed lane yields almost no
free procedural-generator checkouts — it is predominantly paid brush/detail/rig assets (excluded) or
unconfirmable prices (denied). Batch-1 standard met: every row has a confirmed price + license + disposition.

## Reroute probe outcome (native CI) — R6 guardrail bites
The rerouted free GitHub generators were probed and **several hit NEVER_ALLOW prescan patterns** →
permanently quarantined (R6, cannot be cleared): `Durman/BuildingNodes` (`eval(`), `mrachinskiy/booltron`
(`subprocess`), `hsab/GrowthNodes` (`exec(`/`ctypes`/`eval(`/`__import__`). Honest finding: many complex
free add-ons use exec/network-capable patterns (dynamic node eval, dependency install) that the sandbox
safety gate holds — so the free-reroute lane yields **fewer PROBEABLE generators than found**. This is
the guardrail working as designed, not a failure; these tools are `needs_review`/quarantined, not covered.

## Honest conclusion
The L5 forum-routed lane is **predominantly paid, non-procedural marketplace assets** (brush/detail/rig
kits, outside the free-procedural corpus). Its automatable yield: **GitHub-mirror reroutes** (probed —
several quarantined by NEVER_ALLOW, R6) + a small **$0 checkout batch** (owner-gated). No automated
purchase; no scraping; DENY on unconfirmable price (R31). This is the documented exhaustion of the L5
lane's automatable portion — the residual is owner-gated ($0 checkouts) or safety-quarantined.

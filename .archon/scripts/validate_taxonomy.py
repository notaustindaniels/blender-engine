# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""Deterministic taxonomy validator (SPEC §0 parse-taxonomy repurposed to VALIDATE, per the
2026-07-05 kickoff amendment §12.1(3)). The owner delivers inputs/taxonomy.yaml as a finished
file; this checks it against the SPEC §4.1 schema + additive keys and the meta counts, and
prints the wave-1 gate denominators. Tolerant of unknown keys. Exit 0 iff all checks pass.

Usage: uv run .archon/scripts/validate_taxonomy.py [path/to/taxonomy.yaml]
Emits a human report to stderr and a JSON summary to stdout (for archon node output).
"""
import sys, json, pathlib
import yaml

V2_VERBS = ["generate", "scatter", "trace", "stack", "accumulate", "branch",
            "fill", "deplete", "reveal", "illuminate", "simulate", "deform", "aggregate"]


def wave_of(niche: dict) -> int:
    return int(niche.get("wave", 1))


def main() -> int:
    path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "inputs/taxonomy.yaml")
    errors, warnings = [], []
    if not path.exists():
        print(json.dumps({"ok": False, "errors": [f"missing file: {path}"]}))
        print(f"FAIL: taxonomy file not found: {path}", file=sys.stderr)
        return 1

    doc = yaml.safe_load(path.read_text())
    meta = doc.get("meta", {}) or {}
    cats = doc.get("categories", []) or []

    # --- verb enum ---
    enum = meta.get("verb_enum", [])
    if enum != V2_VERBS:
        errors.append(f"meta.verb_enum != frozen v2 enum. got {enum}")
    if "aggregate" not in enum:
        errors.append("meta.verb_enum missing 'aggregate' (§4.4 amendment)")
    verbset = set(enum) | set(V2_VERBS)

    # --- walk niches ---
    ids = {}
    wave1 = wave2 = 0
    reconstructed = core = empty_verb = 0
    declared_sum = unrecovered_sum = 0
    per_cat = {}
    for cat in cats:
        cid = cat.get("id", "?")
        if "declared_count" in cat:
            declared_sum += int(cat["declared_count"])
        if "unrecovered_count" in cat:
            unrecovered_sum += int(cat["unrecovered_count"])
        c_w1 = c_w2 = 0
        for n in cat.get("niches", []) or []:
            nid = n.get("id")
            if not nid:
                errors.append(f"[{cid}] niche with no id: {n}")
                continue
            if nid in ids:
                errors.append(f"duplicate niche id '{nid}' (also in {ids[nid]})")
            ids[nid] = cid
            w = wave_of(n)
            if w == 1:
                wave1 += 1; c_w1 += 1
            elif w == 2:
                wave2 += 1; c_w2 += 1
            else:
                errors.append(f"[{cid}] niche '{nid}' has unexpected wave={w}")
            verbs = n.get("verbs", None)
            if verbs is None:
                errors.append(f"[{cid}] niche '{nid}' has no verbs key (use [] for pure-utility)")
            else:
                if verbs == []:
                    empty_verb += 1
                for v in verbs:
                    if v not in verbset:
                        errors.append(f"[{cid}] niche '{nid}' uses verb '{v}' not in enum")
            if n.get("reconstructed"):
                reconstructed += 1
            if n.get("core"):
                core += 1
        per_cat[cid] = {"name": cat.get("name", ""), "wave1": c_w1, "wave2": c_w2,
                        "declared_count": cat.get("declared_count"),
                        "unrecovered_count": cat.get("unrecovered_count", 0)}

    # --- meta cross-checks ---
    def check(label, computed, declared):
        if declared is None:
            warnings.append(f"meta.{label} absent (computed={computed})")
        elif int(declared) != computed:
            errors.append(f"meta.{label}={declared} but computed={computed}")

    check("wave1_present", wave1, meta.get("wave1_present"))
    check("wave2_present", wave2, meta.get("wave2_present"))
    check("present_total", wave1 + wave2, meta.get("present_total"))
    check("declared_total", declared_sum, meta.get("declared_total"))
    check("unrecovered_total", unrecovered_sum, meta.get("unrecovered_total"))

    # identity: declared_total - unrecovered_total - crossref_dedup_total == wave1_present
    dedup = int(meta.get("crossref_dedup_total", 0))
    ident = declared_sum - unrecovered_sum - dedup
    if ident != wave1:
        errors.append(f"identity check failed: declared({declared_sum}) - unrecovered({unrecovered_sum}) "
                      f"- dedup({dedup}) = {ident} != wave1_present({wave1})")

    # --- step-3 gate denominators (wave-1 only) ---
    terrain_w1 = per_cat.get("terrain", {}).get("wave1", 0)
    veg_w1 = per_cat.get("vegetation", {}).get("wave1", 0)
    gate_denom = terrain_w1 + veg_w1

    summary = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {"wave1_present": wave1, "wave2_present": wave2, "total": wave1 + wave2,
                   "declared_total": declared_sum, "unrecovered_total": unrecovered_sum,
                   "reconstructed": reconstructed, "core": core, "empty_verb_niches": empty_verb,
                   "categories": len(cats), "unique_ids": len(ids)},
        "gate": {"terrain_wave1": terrain_w1, "vegetation_wave1": veg_w1,
                 "terrain_veg_wave1_denominator": gate_denom},
        "per_category": per_cat,
    }
    print(json.dumps(summary, indent=2))

    # human report on stderr
    p = lambda *a: print(*a, file=sys.stderr)
    p("=" * 66)
    p(f"TAXONOMY VALIDATION — {path}")
    p("=" * 66)
    p(f"categories={len(cats)}  unique niche ids={len(ids)}")
    p(f"wave-1 present={wave1}  wave-2 present={wave2}  total={wave1+wave2}")
    p(f"declared_total={declared_sum}  unrecovered_total={unrecovered_sum}  crossref_dedup={dedup}")
    p(f"identity (declared-unrecovered-dedup)={ident}  vs wave1_present={wave1}  -> "
      f"{'OK' if ident==wave1 else 'MISMATCH'}")
    p(f"reconstructed={reconstructed}  core={core}  pure-utility(verbs:[])={empty_verb}")
    p(f"STEP-3 GATE denominator (Terrain+Vegetation wave-1) = "
      f"{terrain_w1}+{veg_w1} = {gate_denom} niches")
    if warnings:
        p("WARNINGS:"); [p("  -", w) for w in warnings]
    if errors:
        p("ERRORS:"); [p("  -", e) for e in errors]
        p("RESULT: FAIL")
        return 1
    p("RESULT: PASS — taxonomy is schema- and count-consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""l6_full_sweep.py — the EXHAUSTIVE L6 sweep executor (D-008 R46+R11). Processes EVERY candidate in
candidates/L6.jsonl in promise order (score-desc): acquire (BlenderKit, scene_uuid+UA) → prescan (R6)
→ gate (materials=shader-probe, node-groups=GN-gate, each with a hard outer timeout) → write a manifest
with the gate state → name-map to a niche ONLY on a genuine match (R14). RESUMABLE: skips candidates
that already have a manifest, so it advances across bounded batches/turns/sessions until all 773 are
gated. The redundant long-tail adds no NEW niche coverage but satisfies R46 "every candidate gated +
indexed"; the CI wave (l6-wave.yml) does the same far faster once the owner adds the secret.

Usage: l6_full_sweep.py --limit 6   (process up to N un-gated candidates this run)
"""
import os, sys, json, urllib.request, urllib.parse, pathlib, hashlib, subprocess, shutil, argparse, re
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SUID = "00000000-0000-0000-0000-000000000001"; UA = "BlenderKit/3.12.3 Blender/4.5"
TAX = yaml.safe_load(open(ROOT / "inputs/taxonomy.yaml"))
DISTINCT = json.loads((ROOT / "inputs/enrich-distinctive.json").read_text()) if (ROOT / "inputs/enrich-distinctive.json").exists() else {}
# niche id -> its distinctive tokens (for honest name->niche mapping)
NICHE_TOK = {}
STOP = {"generator", "shader", "procedural", "material", "kit", "system", "tool", "pack", "the", "and"}
for c in TAX["categories"]:
    for n in (c.get("niches") or []):
        toks = [t for t in re.split(r"[_\s\-]+", n["id"]) if t and t not in STOP and len(t) > 3]
        for t in toks:
            NICHE_TOK.setdefault(t, set()).add(n["id"])


def key():
    for line in open(ROOT / ".archon/.env"):
        if line.startswith("BLENDERKIT_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("BLENDERKIT_API_KEY", "")


H = {"Authorization": f"Bearer {key()}"}


def api(u):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=50))
    except Exception as e:
        return {"_error": str(e)}


def name_to_niche(name):
    """Honest name->niche: a niche whose distinctive token appears in the asset name. R14 — only genuine."""
    t = (name or "").lower()
    hits = {}
    for tok, niches in DISTINCT.items():
        if re.search(rf"\b{re.escape(tok)}\b", t):
            for nz in niches:
                hits[nz] = hits.get(nz, 0) + 2
    for tok, niches in NICHE_TOK.items():
        if re.search(rf"\b{re.escape(tok)}\b", t):
            for nz in niches:
                hits[nz] = hits.get(nz, 0) + 1
    if not hits:
        return None
    best = max(hits.values())
    return sorted([n for n, s in hits.items() if s == best])[0] if best >= 2 else None


def acquire(bid):
    d = api("https://www.blenderkit.com/api/v1/search/?query=" + urllib.parse.quote(f"asset_base_id:{bid}") + "&page_size=1")
    r = (d.get("results") or [])
    if not r:
        return None, None
    m = r[0]
    bf = next((f for f in (m.get("files") or []) if f.get("fileType") == "blend"), None)
    if not bf:
        return None, m
    dl = api(bf["downloadUrl"] + f"?scene_uuid={SUID}")
    url = dl.get("filePath")
    if not url:
        return None, m
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read(), m
    except Exception:
        return None, m


def gate(kind, blend_path, cid):
    """Robust single-candidate gate with a hard outer timeout (Blender render can block the inner cap)."""
    runner = "run_shader.sh" if kind == "material" else "run_probe.sh"
    marker = "SHADER_RESULT_JSON" if kind == "material" else "RESULT_JSON"
    name = f"l6f-{cid}"[:40]
    try:
        r = subprocess.run(["bash", str(ROOT / "sandbox" / runner), "4.5", str(blend_path), name, "70"],
                           capture_output=True, text=True, timeout=95)
        line = [l for l in r.stdout.splitlines() if marker in l]
        return json.loads(line[0].split(marker + ":")[1]) if line else {"state": "noresult"}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True)
        return {"state": "quarantine_timeout"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=6); a = ap.parse_args()
    rows = [json.loads(l) for l in open(ROOT / "candidates/L6.jsonl") if l.strip()]
    rows = [r for r in rows if r.get("procedural")]   # materials + node-groups (models are A-lane)
    processed = 0
    for r in rows:
        if processed >= a.limit:
            break
        cid = r["canonical_id"]
        if (ROOT / f"manifests/{cid}.json").exists():
            continue
        data, m = acquire(r.get("source_id"))
        if not data:
            # unacquirable -> record a graveyard-style manifest so it's not retried forever (gated=fail)
            json.dump({"canonical_id": cid, "name": r.get("name"), "artifact_type": r["asset_type"],
                       "verify": {"4.5": {"state": "fail", "operators": [], "render_ok": False}},
                       "enrich_note": "L6: unacquirable (no blend/url)"}, open(ROOT / f"manifests/{cid}.json", "w"), indent=2)
            processed += 1; print(f"  {cid[:40]}: unacquirable", flush=True); continue
        dd = ROOT / f"vault/{cid}/1.0"; dd.mkdir(parents=True, exist_ok=True)
        fn = "material.blend" if r["asset_type"] == "material" else "nodegroup.blend"
        (dd / fn).write_bytes(data); sha = hashlib.sha256(data).hexdigest()
        lic = (m or {}).get("license") or r.get("usage_license")
        json.dump({"canonical_id": cid, "name": r.get("name"), "entry_type": r["asset_type"], "procedural": True,
                   "lane": "L6", "usage_license": lic, "attribution": f'"{r.get("name")}" — BlenderKit ({lic}) — Article-5 no-export',
                   "file": fn, "sha256": sha}, open(dd / "meta.json", "w"), indent=2)
        st = gate("material" if r["asset_type"] == "material" else "nodegroup", dd / fn, cid)
        state = st.get("state", "fail")
        niche = name_to_niche(r.get("name")) if state in ("pass", "partial") else None
        man = {"canonical_id": cid, "name": r.get("name"), "artifact_type": r["asset_type"],
               "verify": {"4.5": {"state": state, "operators": [], "render_ok": st.get("render_ok", state == "pass"),
                                  "shader_delta": st.get("delta")}},
               "enriched_by": "L6 full-sweep GN/shader gate (D-008)",
               "enrich_note": f"L6 full-sweep: {r['asset_type']} gated {state}" + (f" -> {niche}" if niche else " (no niche name-match)")}
        if niche and state == "pass":
            man["operators_enriched"] = [{"kind": "material" if r["asset_type"] == "material" else "gn_node_group",
                                          "id": f"{cid}:{r['asset_type']}", "verbs": ["fill" if r["asset_type"] == "material" else "generate"],
                                          "niches": [niche], "quality": "full_generator"}]
        json.dump(man, open(ROOT / f"manifests/{cid}.json", "w"), indent=2)
        processed += 1
        print(f"  {cid[:34]:34} {state} {'-> '+niche if niche else ''}", flush=True)
    remaining = sum(1 for r in rows if not (ROOT / f"manifests/{r['canonical_id']}.json").exists())
    print(json.dumps({"processed_this_run": processed, "remaining_ungated": remaining, "total_procedural": len(rows)}))


if __name__ == "__main__":
    main()

# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""verify_matrix.py — the Gate orchestrator (SPEC §6.1 `verify` node; §5.1/§5.2/§3.2).

Deterministic, NO AI. For each artifact:
  1. PRESCAN (SPEC §3.4, gate precondition) unless --no-gate. `needs_review` artifacts are
     skipped UNLESS listed (with rationale) in the human-clearance file (--clearances).
  2. For each Blender version, run probe.py in the sandbox via run_probe.sh (all containment
     flags live there). Enforce an OUTER wall-clock cap; on timeout, `docker kill` the
     container and record `quarantine`.
  3. Write manifests/<canonical_id>.json in the SPEC §4.3 `verify` shape.

Usage:
  uv run .archon/scripts/verify_matrix.py --artifacts <dir|jsonl> [--out manifests] \
      [--versions 3.6,4.2,4.5] [--no-gate] [--clearances reviews/prescan_clearances.yaml] \
      [--timeout 150] [--json-summary path]

--artifacts: a directory of artifact files, OR a normalized.jsonl (each row: canonical_id, file/path).
"""
import argparse, json, os, re, subprocess, sys, pathlib, datetime, zipfile
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN_PROBE = ROOT / "sandbox" / "run_probe.sh"
PRESCAN = ROOT / ".archon" / "scripts" / "prescan.py"
RESULT_RE = re.compile(r"PROBE_RESULT_JSON:(\{.*\})")
VER_TUPLE = {"3.6": (3, 6), "4.2": (4, 2), "4.5": (4, 5)}


def _inspect_zip(path):
    """Lightweight: (addon_type, min_tuple) from a zip's manifest/bl_info, without a container."""
    if not path.lower().endswith(".zip"):
        return "other", None
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return "broken", None
    names = z.namelist()
    man = [n for n in names if n.endswith("blender_manifest.toml")]
    if man:
        txt = z.read(man[0]).decode("utf-8", "ignore")
        m = re.search(r'blender_version_min\s*=\s*"(\d+)\.(\d+)', txt)
        return "extension_manifest", ((int(m.group(1)), int(m.group(2))) if m else None)
    for n in names:
        if n.endswith(".py"):
            txt = z.read(n).decode("utf-8", "ignore")
            if "bl_info" in txt:
                m = re.search(r'"blender"\s*:\s*\(\s*(\d+)\s*,\s*(\d+)', txt)
                return "legacy", ((int(m.group(1)), int(m.group(2))) if m else None)
    return "other", None


def artifact_compat(path):
    """Prefer vault meta.json (addon_type + declared_blender_min); fall back to inspecting the zip."""
    typ, mn = "other", None
    meta = pathlib.Path(path).parent / "meta.json"
    if meta.exists():
        try:
            d = json.loads(meta.read_text())
            typ = d.get("addon_type") or typ
            dm = d.get("declared_blender_min")
            if dm:
                p = str(dm).split(".")
                mn = (int(p[0]), int(p[1]) if len(p) > 1 else 0)
        except Exception:
            pass
    if typ == "other" or mn is None:
        t2, m2 = _inspect_zip(path)
        typ = t2 if typ == "other" else typ
        mn = m2 if mn is None else mn
    return {"type": typ, "min": mn}


def incompatible(compat, ver):
    """Owner rider 4: return a reason string if this Blender version is impossible for the artifact."""
    vt = VER_TUPLE.get(ver)
    if not vt:
        return None
    if compat["type"] in ("extension_manifest", "extension") and vt < (4, 2):
        return "manifest extension needs Blender 4.2+ (no extension system on 3.6)"
    if compat["min"] and compat["min"] > vt:
        return f"declared min {'.'.join(map(str, compat['min']))} > {ver}"
    return None


def run_prescan(artifact):
    try:
        p = subprocess.run(["uv", "run", str(PRESCAN), artifact],
                           capture_output=True, text=True, timeout=60)
        data = json.loads(p.stdout)
        return data[0] if data else {"status": "error", "hits": []}
    except Exception as e:
        return {"status": "error", "hits": [], "error": str(e)}


def run_probe(ver, artifact, cid, timeout):
    name = f"probe-{cid}-{ver}".replace("/", "_").replace(".", "-")[:56]
    cap = max(60, timeout - 40)   # internal probe SIGALRM cap < outer subprocess timeout
    try:
        p = subprocess.run(["bash", str(RUN_PROBE), ver, artifact, name, str(cap)],
                           capture_output=True, text=True, timeout=timeout)
        for line in p.stdout.splitlines():
            m = RESULT_RE.search(line)
            if m:
                return json.loads(m.group(1))
        return {"state": "quarantine", "operators": [], "render_ok": False,
                "notes": "no PROBE_RESULT_JSON emitted", "stderr_tail": p.stderr[-400:]}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True)
        return {"state": "quarantine_timeout", "operators": [], "render_ok": False,
                "notes": f"outer wall-clock cap {timeout}s exceeded -> docker kill"}
    except Exception as e:
        return {"state": "quarantine", "operators": [], "render_ok": False, "notes": f"orchestrator error: {e}"}


def load_artifacts(spec):
    """Return list of (canonical_id, path)."""
    p = pathlib.Path(spec)
    out = []
    if p.is_dir():
        for f in sorted(p.rglob("*")):     # recursive: handles nested vault/<cid>/<ver>/<file>
            if f.suffix.lower() in (".zip", ".py", ".blend"):
                cid = f.stem
                meta = f.parent / "meta.json"
                if meta.exists():
                    try:
                        cid = json.loads(meta.read_text()).get("canonical_id", f.stem)
                    except Exception:
                        pass
                out.append((cid, str(f)))
    elif p.suffix == ".jsonl":
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            path = row.get("path") or row.get("file")
            if not path:
                continue   # skip rows with no local artifact (already-vaulted / deferred)
            cid = row.get("canonical_id") or pathlib.Path(path).stem
            out.append((cid, path))
    else:
        out.append((p.stem, str(p)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", required=True)
    ap.add_argument("--out", default="manifests")
    ap.add_argument("--versions", default="3.6,4.2,4.5")
    ap.add_argument("--no-gate", action="store_true")
    ap.add_argument("--clearances", default="reviews/prescan_clearances.yaml")
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--json-summary", default="")
    a = ap.parse_args()

    versions = [v.strip() for v in a.versions.split(",") if v.strip()]
    cleared = set()
    cp = ROOT / a.clearances
    if cp.exists():
        doc = yaml.safe_load(cp.read_text()) or {}
        cleared = {c["artifact"] for c in doc.get("cleared", [])}

    outdir = ROOT / a.out
    outdir.mkdir(parents=True, exist_ok=True)
    artifacts = load_artifacts(a.artifacts)
    summary = []

    for cid, path in artifacts:
        base = os.path.basename(path)
        rec = {"canonical_id": cid, "artifact": base, "verify": {}, "operators": [],
               "prescan": "skipped", "artifact_type": None,
               "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}

        gated_out = False
        if not a.no_gate:
            pre = run_prescan(path)
            rec["prescan"] = pre["status"]
            rec["prescan_hits"] = [h["pattern"] for h in pre.get("hits", [])]
            if pre["status"] == "needs_review":
                if base in cleared:
                    rec["prescan"] = "cleared"
                else:
                    gated_out = True

        if gated_out:
            for v in versions:
                rec["verify"][v] = {"state": "needs_review", "operators": [], "render_ok": False}
            print(f"  {cid:26} GATED (needs_review): {rec['prescan_hits']}", file=sys.stderr)
        else:
            compat = artifact_compat(path)          # rider 4: version-aware skipping
            rec["artifact_type"] = compat["type"]
            rec["declared_min"] = ".".join(map(str, compat["min"])) if compat["min"] else None
            ops_union = set()
            for v in versions:
                why = incompatible(compat, v)
                if why:
                    rec["verify"][v] = {"state": "skipped_incompatible", "operators": [],
                                        "render_ok": False, "reason": why}
                    continue
                r = run_probe(v, path, cid, a.timeout)
                if r.get("state") == "quarantine_timeout":     # rider 5: one retry at 2x cap
                    r = run_probe(v, path, cid, a.timeout * 2)
                    r["retried_2x"] = True
                cell = {"state": r.get("state"), "operators": r.get("operators", []),
                        "render_ok": r.get("render_ok", False)}
                if r.get("retried_2x"):
                    cell["retried_2x"] = True
                rec["verify"][v] = cell
                ops_union |= set(r.get("operators", []))
            rec["operators"] = sorted(ops_union)
            states = " ".join(f"{v}:{rec['verify'][v]['state']}" for v in versions)
            print(f"  {cid:26} {states}", file=sys.stderr)

        (outdir / f"{cid}.json").write_text(json.dumps(rec, indent=2))
        summary.append(rec)

    if a.json_summary:
        pathlib.Path(a.json_summary).write_text(json.dumps(summary, indent=2))
    print(json.dumps({"artifacts": len(summary), "out": str(outdir), "versions": versions}))


if __name__ == "__main__":
    main()

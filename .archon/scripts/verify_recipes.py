# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""verify_recipes.py — the recipe-probe orchestrator (D-003 R21). For each recipe in recipes.yaml,
resolve each step's artifact_cid to a vaulted zip, run probe_recipe.py in the sandbox on the best
available Blender version, and set tier=recipe_verified ONLY if the recipe-probe produced geometry
+ render. Never promotes on hand-wave; a recipe that can't be driven stays recipe_unverified.
Deterministic, no AI. Rewrites inputs/recipes.yaml tiers in place; writes reports/recipe-verify.json.

Usage: verify_recipes.py [--versions 4.5,4.2] [--timeout 150]
"""
import argparse, json, subprocess, sys, glob, pathlib, re
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN_RECIPE = ROOT / "sandbox" / "run_recipe.sh"
VAULT = ROOT / "vault"
RESULT_RE = re.compile(r"RECIPE_RESULT_JSON:(\{.*\})")


def find_artifact(cid):
    hits = sorted(glob.glob(str(VAULT / cid / "*" / "*.zip")))
    return hits[0] if hits else None


def resolve_recipe(r):
    """Build the container-path recipe JSON; return (json, mounts_ok) or (None, missing)."""
    steps, missing = [], []
    for st in r.get("steps", []):
        if st.get("builtin"):
            steps.append({"builtin": st["builtin"]})
            continue
        cid = st.get("artifact_cid")
        art = find_artifact(cid) if cid else None
        if cid and not art:
            missing.append(cid)
            continue
        step = {"op": st.get("op")}
        if art:
            # container sees the vault mounted at /work/vault
            rel = pathlib.Path(art).relative_to(VAULT)
            step["artifact"] = f"/work/vault/{rel}"
        if st.get("params"):
            step["params"] = st["params"]
        steps.append(step)
    return {"niche": r["niche"], "steps": steps}, missing


def run_one(recipe_json, ver, timeout):
    name = None
    try:
        p = subprocess.run(["bash", str(RUN_RECIPE), ver, json.dumps(recipe_json), str(VAULT), str(max(60, timeout - 40))],
                           capture_output=True, text=True, timeout=timeout)
        for line in p.stdout.splitlines():
            m = RESULT_RE.search(line)
            if m:
                return json.loads(m.group(1))
        return {"state": "recipe_unverified", "notes": "no RECIPE_RESULT_JSON", "stderr": p.stderr[-300:]}
    except subprocess.TimeoutExpired:
        return {"state": "recipe_unverified", "notes": f"timeout {timeout}s"}
    except Exception as e:
        return {"state": "recipe_unverified", "notes": f"orchestrator error: {e}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versions", default="4.5,4.2")
    ap.add_argument("--timeout", type=int, default=150)
    a = ap.parse_args()
    versions = [v.strip() for v in a.versions.split(",") if v.strip()]

    doc = yaml.safe_load((ROOT / "inputs/recipes.yaml").read_text())
    results = []
    for r in doc.get("recipes", []):
        rj, missing = resolve_recipe(r)
        if missing:
            r["tier"] = "recipe_unverified"
            results.append({"niche": r["niche"], "state": "recipe_unverified",
                            "notes": f"artifact(s) not vaulted: {missing}"})
            print(f"  {r['niche']:28} recipe_unverified (missing {missing})", file=sys.stderr)
            continue
        best = {"state": "recipe_unverified", "notes": "no version drove it"}
        for ver in versions:
            res = run_one(rj, ver, a.timeout)
            if res.get("state") == "recipe_verified":
                best = res; best["blender"] = ver; break
            best = res
        r["tier"] = best["state"]
        results.append({"niche": r["niche"], "state": best["state"], "notes": best.get("notes", "")})
        print(f"  {r['niche']:28} {best['state']}  {best.get('notes','')[:60]}", file=sys.stderr)

    (ROOT / "inputs/recipes.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, width=120))
    (ROOT / "reports/recipe-verify.json").write_text(json.dumps(results, indent=2))
    verified = [x["niche"] for x in results if x["state"] == "recipe_verified"]
    print(json.dumps({"recipes": len(results), "verified": len(verified), "verified_niches": verified}))


if __name__ == "__main__":
    main()

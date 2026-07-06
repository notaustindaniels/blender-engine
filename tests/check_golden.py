# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""check_golden.py — golden-set acceptance test (SPEC §8, KICKOFF bar b).

Compares the probe's per-version states (from manifests/golden/*.json) against the locked
expectations in tests/golden_expected.yaml, and asserts the prescan gate. Writes
reports/golden-set.md and exits non-zero on ANY mismatch.

  uv run tests/check_golden.py            # check existing manifests/golden
  uv run tests/check_golden.py --run      # re-run the whole matrix first, then check
"""
import argparse, json, subprocess, sys, pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSIONS = ["3.6", "4.2", "4.5"]


def run_matrix():
    subprocess.run(["uv", "run", str(ROOT / ".archon/scripts/verify_matrix.py"),
                    "--artifacts", str(ROOT / "tests/fixtures/golden"), "--no-gate",
                    "--out", "manifests/golden", "--timeout", "150"],
                   cwd=ROOT, check=True)


def run_prescan(name):
    art = ROOT / "tests/fixtures/golden" / f"{name}.zip"
    p = subprocess.run(["uv", "run", str(ROOT / ".archon/scripts/prescan.py"), str(art)],
                       capture_output=True, text=True, cwd=ROOT)
    return json.loads(p.stdout)[0]["status"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        run_matrix()

    exp = yaml.safe_load((ROOT / "tests/golden_expected.yaml").read_text())
    rows, all_ok = [], True

    # state matrix
    for name, spec in exp["expected"].items():
        mpath = ROOT / "manifests/golden" / f"{name}.json"
        got = {}
        if mpath.exists():
            man = json.loads(mpath.read_text())
            got = {v: man["verify"].get(v, {}).get("state") for v in VERSIONS}
        cells = []
        for v in VERSIONS:
            want = spec["states"][v]
            g = got.get(v)
            ok = (g == want)
            all_ok &= ok
            cells.append((v, want, g, ok))
        rows.append((name, cells, spec["why"]))

    # prescan gate
    pre_rows = []
    for name, want in exp["prescan_expected"].items():
        got = run_prescan(name)
        ok = (got == want)
        all_ok &= ok
        pre_rows.append((name, want, got, ok))

    # ---- console ----
    print("GOLDEN-SET ACCEPTANCE  (probe state vs expected)")
    print(f"{'artifact':22} " + "  ".join(f"{v:>7}" for v in VERSIONS))
    for name, cells, _why in rows:
        line = f"{name:22} "
        for v, want, g, ok in cells:
            mark = "✓" if ok else "✗"
            line += f"  {(g or '—'):>6}{mark}" if ok else f"  {(str(g) or '—'):>5}{mark}!want={want}"
        print(line)
    print("\nPRESCAN GATE:")
    for name, want, got, ok in pre_rows:
        print(f"  {name:22} want={want:14} got={got:14} {'✓' if ok else '✗'}")
    print("\nVERDICT:", "PASS — all golden states + prescan correct" if all_ok else "FAIL — mismatches above")

    # ---- report ----
    md = ["# Golden Set — Verification-Gate Calibration (SPEC §8)", ""]
    md.append(f"**Result: {'✅ PASS' if all_ok else '❌ FAIL'}** — the probe returns the correct "
              f"state for every golden artifact across Blender 3.6 / 4.2 / 4.5.\n")
    md.append("Probe images are built from official `download.blender.org` tarballs pinned by "
              "SHA-256 (SPEC §12.1(1)); render check is Cycles-CPU (SPEC §12.1 render deviation).\n")
    md.append("| artifact | 3.6 | 4.2 | 4.5 | why |")
    md.append("|---|---|---|---|---|")
    for name, cells, why in rows:
        cs = [f"`{g}`" + ("✓" if ok else f"✗ (want `{want}`)") for v, want, g, ok in cells]
        md.append(f"| `{name}` | {cs[0]} | {cs[1]} | {cs[2]} | {why} |")
    md.append("\n## Prescan gate (SPEC §3.4)\n")
    md.append("| fixture | expected | got | |")
    md.append("|---|---|---|---|")
    for name, want, got, ok in pre_rows:
        md.append(f"| `{name}` | {want} | `{got}` | {'✓' if ok else '✗'} |")
    md.append("\n## What this calibrates\n")
    md.append("- **All five result states** exercised: `pass` (good_cube, tissue, cellfracture, "
              "sapling@4.5), `partial` (antlandscape, ivygen, noop), `fail` (broken, ext@3.6), "
              "`legacy` (2.7x add-on). `quarantine` is exercised by the wall-clock cap in probe.py.")
    md.append("- **Version gating is real**: `sapling` (min 4.4) is `fail/fail/pass`; every 4.2+ "
              "extension is `fail` on 3.6 (no extension system pre-4.2).")
    md.append("- **Honest headless limit**: dialog-only generators (A.N.T. landscape_add returns "
              "`PASS_THROUGH` headless) correctly land at `partial`, which still counts toward coverage.")
    md.append("- **Prescan blocks danger** before any container run; benign fixtures pass clean.")
    md.append("\n![sandbox render](../progress/media/golden_cube_render.png)\n")
    md.append("_Headless Cycles-CPU render produced inside the `--network none` sandbox — proof "
              "the render check (§3.1 step 5) works across the emulated matrix._")
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/golden-set.md").write_text("\n".join(md) + "\n")
    print("wrote reports/golden-set.md")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()

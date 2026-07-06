# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""build_index.py — rebuild corpus.db from JSON (SPEC §4.5, §2.1 Map). IDEMPOTENT: JSON
manifests + vault meta.json are canonical; the DB is disposable and always reproducible.
Deterministic, no AI. Prints a content-hash so the idempotency test can assert two runs match.

Tables: addons, operators, verify, coverage, graveyard (SPEC §4.5).

Usage: build_index.py [--manifests manifests] [--vault vault] [--db corpus.db] [--graveyard graveyard.jsonl]
"""
import argparse, json, glob, os, sqlite3, hashlib, pathlib

SURVIVE = {"pass", "partial"}

DDL = """
CREATE TABLE addons(canonical_id TEXT PRIMARY KEY, name TEXT, author TEXT, license TEXT,
                    addon_type TEXT, procedural INTEGER);
CREATE TABLE operators(id TEXT PRIMARY KEY, canonical_id TEXT, kind TEXT, op_id TEXT, verbs_json TEXT);
CREATE TABLE verify(canonical_id TEXT, blender_ver TEXT, state TEXT, render_ok INTEGER,
                    PRIMARY KEY(canonical_id, blender_ver));
CREATE TABLE coverage(niche_id TEXT, canonical_id TEXT, operator_id TEXT, blender_ver TEXT);
CREATE TABLE graveyard(url TEXT, reason TEXT, seen_at TEXT);
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", default="manifests")
    ap.add_argument("--vault", default="vault")
    ap.add_argument("--db", default="corpus.db")
    ap.add_argument("--graveyard", default="graveyard.jsonl")
    a = ap.parse_args()

    if os.path.exists(a.db):
        os.remove(a.db)
    con = sqlite3.connect(a.db)
    con.executescript(DDL)

    # provenance (addons) from vault meta.json
    metas = {}
    for mp in sorted(glob.glob(os.path.join(a.vault, "*", "*", "meta.json"))):
        m = json.loads(open(mp).read())
        metas[m["canonical_id"]] = m

    # verification+capability from manifests
    manifests = {}
    for mp in sorted(glob.glob(os.path.join(a.manifests, "*.json"))):
        m = json.loads(open(mp).read())
        manifests[m["canonical_id"]] = m

    addons, ops, verifies, covers = [], [], [], []
    for cid in sorted(set(metas) | set(manifests)):
        meta = metas.get(cid, {})
        man = manifests.get(cid, {})
        addons.append((cid, meta.get("name") or man.get("name"), meta.get("author"),
                       meta.get("license"), meta.get("addon_type") or man.get("artifact_type"),
                       1 if meta.get("procedural") else 0))
        # per-version verify
        surviving_vers = set()
        for ver, vres in sorted((man.get("verify") or {}).items()):
            st = vres.get("state")
            verifies.append((cid, ver, st, 1 if vres.get("render_ok") else 0))
            if st in SURVIVE:
                surviving_vers.add(ver)
        # operators + coverage (niche <- passing operator on surviving versions)
        for op in (man.get("operators_enriched") or man.get("operators") or []):
            if isinstance(op, str):
                op = {"kind": "bpy_op", "id": op, "verbs": [], "niches": []}
            opid = f"{cid}:{op.get('id')}"
            ops.append((opid, cid, op.get("kind", "bpy_op"), op.get("id"),
                        json.dumps(op.get("verbs", []))))
            for niche in op.get("niches", []):
                for ver in sorted(surviving_vers):
                    covers.append((niche, cid, opid, ver))

    con.executemany("INSERT OR IGNORE INTO addons VALUES(?,?,?,?,?,?)", sorted(set(addons)))
    con.executemany("INSERT OR IGNORE INTO operators VALUES(?,?,?,?,?)", sorted(set(ops)))
    con.executemany("INSERT OR IGNORE INTO verify VALUES(?,?,?,?)", sorted(set(verifies)))
    con.executemany("INSERT INTO coverage VALUES(?,?,?,?)", sorted(set(covers)))

    if os.path.exists(a.graveyard):
        for line in open(a.graveyard):
            if line.strip():
                g = json.loads(line)
                con.execute("INSERT INTO graveyard VALUES(?,?,?)",
                            (g.get("url"), g.get("reason"), g.get("seen_at")))
    con.commit()

    # deterministic content hash (logical dump)
    h = hashlib.sha256()
    for line in con.iterdump():
        if line.startswith("INSERT") or line.startswith("CREATE"):
            h.update(line.encode())
    con.close()
    digest = h.hexdigest()
    print(json.dumps({"db": a.db, "addons": len(set(addons)), "operators": len(set(ops)),
                      "verify_rows": len(set(verifies)), "coverage_rows": len(set(covers)),
                      "content_sha256": digest}))


if __name__ == "__main__":
    main()

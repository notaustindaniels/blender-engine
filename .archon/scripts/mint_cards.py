# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""mint_cards.py — mint Tier-1 progressive-disclosure cards (D-008 R52).

A ~120-word card per operator and per recipe on a FIXED template: what it does · verbs · media ·
niches · quality tier · license obligation · param signature · one example invocation · Blender
versions. Deterministic (fills from the manifest/recipe/meta — the enrich JUDGMENT already lives
there; this is not a second AI pass). Cards are committed to cards/<id>.md (Tier-1) and ingested as
chunks by kb_build.py. Tier-0 = CORPUS.md; Tier-2 = the full manifest + doc chunks.

At harvest scale this runs at GATE TIME (enrich mints the card while it holds the README). This script
is the back-fill + the reusable minter. Usage: mint_cards.py [--out cards]
"""
import json, glob, pathlib, sys, yaml

MEDIUM = yaml.safe_load(open("inputs/niche-medium.yaml"))["medium"]
RECIPES = yaml.safe_load(open("inputs/recipes.yaml"))["recipes"]
_TAX = yaml.safe_load(open("inputs/taxonomy.yaml"))
ALIASES = {n["id"]: (n.get("aliases") or []) for c in _TAX["categories"] for n in (c.get("niches") or [])}


def alias_line(niches):
    al = []
    for n in niches:
        al += ALIASES.get(n, [])
    return ", ".join(dict.fromkeys(al)) if al else ""

# license obligation text per license class (from HANDOFF.md §5 — load-bearing)
LIC_OBLIG = {
    "by": "CC-BY — visible attribution required in render credits.",
    "cc-by": "CC-BY — visible attribution required in render credits.",
    "cc0": "CC0 — no attribution required.",
    "by-sa": "CC-BY-SA — attribution + share-alike.",
    "royalty_free": "Royalty-Free (BlenderKit) — rendered-video only, NO 3D-export; incorporation-only.",
    "gpl": "GPL — applies to add-on code, not render output; safe to invoke.",
    "gpl-3.0": "GPL — applies to add-on code, not render output; safe to invoke.",
    "gpl-2.0": "GPL — applies to add-on code, not render output; safe to invoke.",
    None: "license unrecorded — verify before commercial use.",
}


def meta_for(cid):
    for g in glob.glob(f"vault/{cid}/*/meta.json"):
        return json.loads(open(g).read())
    return {}


def lic_text(license_):
    return LIC_OBLIG.get((license_ or "").lower() if license_ else None, f"{license_} — verify obligations.")


def passing_versions(man):
    v = man.get("verify") or {}
    return sorted(k for k, s in v.items() if (s or {}).get("state") in ("pass", "partial"))


def quality_of(op, man):
    if op.get("quality"):
        return op["quality"]
    # a manifest full_pass operator is a full generator; else infer
    vers = passing_versions(man)
    states = {(man.get("verify") or {}).get(x, {}).get("state") for x in vers}
    return "full_generator" if "pass" in states else "partial"


def card_operator(man, op):
    cid = man["canonical_id"]
    niches = op.get("niches") or []
    verbs = op.get("verbs") or []
    media = sorted({MEDIUM.get(n, "?") for n in niches})
    meta = meta_for(cid)
    lic = meta.get("usage_license") or meta.get("license")
    vers = passing_versions(man) or ["4.5"]
    kind = op.get("kind", "bpy_op")
    opid = op.get("id", cid)
    what = (man.get("enrich_note") or man.get("name") or opid).strip().rstrip(".")
    if kind == "bpy_op":
        sig = f"bpy.ops.{opid}(...)"
        example = f">>> bpy.ops.{opid}()  # then tune the redo panel / operator props"
    elif kind == "material":
        sig = f"material '{meta.get('name', opid)}' (procedural node group)"
        example = f"# append material, assign to target, render"
    else:  # gn_node_group / gn_pack
        sig = f"GN node group '{opid}'"
        example = f"# append node group '{opid}', bind to a mesh, set inputs"
    key = f"operator/{cid}::{opid}"
    text = (
        f"# {opid}  ({cid})\n"
        f"**What it does:** {what[:180]}.\n"
        f"**Verbs:** {', '.join(verbs) or '—'}  ·  **Media:** {', '.join(media) or '—'}  ·  "
        f"**Niches:** {', '.join(niches) or '—'}\n"
        f"**Quality:** {quality_of(op, man)}  ·  **License:** {lic_text(lic)}\n"
        f"**Kind:** {kind}  ·  **Params:** {sig}\n"
        f"**Example:** {example}\n"
        f"**Also known as:** {alias_line(niches) or '—'}\n"
        f"**Blender:** {', '.join(vers)}  ·  Tier-2: manifests/{cid}.json"
    )
    return key, text, {"cid": cid, "operator_id": opid, "kind": kind, "verbs": verbs,
                       "niches": niches, "media": media, "quality": quality_of(op, man),
                       "license": lic, "versions": vers}


def card_recipe(r):
    niche = r["niche"]
    medium = MEDIUM.get(niche, "?")
    steps = r.get("steps") or []
    step_desc = []
    lic = None
    for s in steps:
        if "op" in s:
            step_desc.append(f"{s.get('artifact_cid','?')}::{s['op']}")
        elif "builtin" in s:
            step_desc.append(f"builtin:{s['builtin']}")
        elif "import_asset" in s:
            step_desc.append(f"import_asset({pathlib.Path(s['import_asset']).parts[2] if '/' in s['import_asset'] else s['import_asset']})")
            # asset-fed -> capture the asset's license
            cidguess = s["import_asset"].split("/")[3] if s["import_asset"].count("/") >= 3 else None
            if cidguess:
                lic = lic or (meta_for(cidguess).get("usage_license"))
    tier = r.get("tier", "recipe_unverified")
    quality = "asset_fed_minimal" if any("import_asset" in s for s in steps) else "composed"
    key = f"recipe/{niche}"
    text = (
        f"# recipe: {niche}\n"
        f"**What it does:** compose {' + '.join(step_desc)} → {niche}.\n"
        f"**Verbs:** (composition)  ·  **Media:** {medium}  ·  **Niches:** {niche}\n"
        f"**Quality:** {quality} ({tier})  ·  **License:** {lic_text(lic)}\n"
        f"**Steps:** {' ; '.join(step_desc)}\n"
        f"**Also known as:** {alias_line([niche]) or '—'}\n"
        f"**Example:** run .archon/scripts/verify_recipes.py --versions 4.5\n"
        f"**Note:** {(r.get('note') or '')[:120]}"
    )
    return key, text, {"niche": niche, "tier": tier, "quality": quality, "medium": medium,
                       "steps": step_desc, "license": lic, "recipe": True}


def main():
    outdir = pathlib.Path("cards")
    outdir.mkdir(exist_ok=True)
    cards = {}
    for mp in sorted(glob.glob("manifests/*.json")):
        man = json.loads(open(mp).read())
        for op in (man.get("operators_enriched") or []):
            key, text, props = card_operator(man, op)
            cards[key] = {"text": text, "props": props}
    for r in RECIPES:
        key, text, props = card_recipe(r)
        cards[key] = {"text": text, "props": props}
    # write each card to cards/<safe>.md + a manifest index
    for key, c in cards.items():
        safe = key.replace("/", "__").replace("::", "--").replace(".", "_")
        (outdir / f"{safe}.md").write_text(c["text"])
    (outdir / "_index.json").write_text(json.dumps(
        {k: v["props"] for k, v in cards.items()}, indent=1))
    print(json.dumps({"cards_minted": len(cards),
                      "operators": sum(1 for k in cards if k.startswith("operator/")),
                      "recipes": sum(1 for k in cards if k.startswith("recipe/"))}))


if __name__ == "__main__":
    main()

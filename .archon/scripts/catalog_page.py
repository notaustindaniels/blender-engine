# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""catalog_page.py — render THE LIST (D-008 catalog campaign, deliverable face 2). Reads catalog.jsonl
and generates reports/catalog/index.html (filterable/sortable, grouped, badges, live URLs) + CATALOG.md
(fallback). Headline = TOTAL ENTRIES split by status. Regenerated on every ingest; served by serve.sh.
Self-contained HTML (inline CSS/JS), theme-aware, no external requests.

D-009 R56: campaign CLOSED at snapshot-catalog-v1; headline is and remains TOTAL CATALOG ENTRIES
(coverage % is secondary). D-009 R59: the legend distinguishes **gate-verified** (sandbox-proven tool:
real native-CI pass/partial) from **provenance-verified** (license+hash-proven asset / enumeration, the
`prov` badge — never sandbox-run), plus a known-noise note that keyword-derived category tags on
asset/provenance rows may be noisy.
"""
import json, pathlib, html
from collections import Counter
ROOT = pathlib.Path(__file__).resolve().parents[2]

# D-009 R59 verification classes: (class-key, label, color)
GATE_STATES_PASS = ("pass", "partial")


def classify(r):
    """gate-verified (sandbox-proven) vs provenance-verified (license+hash, never sandbox-run)."""
    st = r["status"]
    if st == "auto_acquired_verified":
        if r.get("gate_state") in GATE_STATES_PASS:
            return ("gate", "✓ gate-verified", "#1a7f37")
        return ("prov", "◆ provenance-verified", "#0969da")
    if st == "click_to_get":
        return ("cta", "↓ click-to-get", "#9a6700")
    return ("excl", "✕ excluded", "#82071e")


def main():
    rows = [json.loads(l) for l in open(ROOT / "catalog.jsonl") if l.strip()]
    total = len(rows)
    by_status = Counter(r["status"] for r in rows)
    by_market = Counter(r.get("marketplace") or "?" for r in rows)
    gate_verified = sum(1 for r in rows if r["status"] == "auto_acquired_verified"
                        and r.get("gate_state") in GATE_STATES_PASS)
    prov_verified = by_status.get("auto_acquired_verified", 0) - gate_verified
    cta = by_status.get("click_to_get", 0)
    excl = by_status.get("excluded", 0)

    # ---- CATALOG.md (R56 header: campaign closed, headline = total entries) ----
    md = [f"# THE CATALOG — free procedural Blender tooling\n",
          "_Campaign CLOSED (D-009 R56); `snapshot-catalog-v1` is the tag of record. Headline metric is and "
          "remains TOTAL CATALOG ENTRIES (coverage % is a secondary stat). Growth now runs as standing "
          "engines (`discovery-monthly.yml`), regenerating this file per `wave_ingest.py`._\n",
          f"**TOTAL CATALOG ENTRIES: {total}**  ·  ✓ gate-verified {gate_verified} · "
          f"◆ provenance-verified {prov_verified} · ↓ click-to-get {cta} · ✕ excluded {excl}\n",
          "By marketplace: " + " · ".join(f"{m} {n}" for m, n in by_market.most_common()) + "\n",
          "\n**gate-verified** = sandbox-proven tool (real native-CI pass/partial). "
          "**provenance-verified** = license+hash-proven asset/enumeration, never sandbox-run (the `prov` "
          "badge). Category tags on asset/provenance rows are keyword-derived and may be noisy — hints, not "
          "gate-verified capability tags.\n",
          "\n_Full filterable page: reports/catalog/index.html (served at /catalog.html)._\n"]
    (ROOT / "CATALOG.md").write_text("\n".join(md))

    # ---- index.html ----
    def esc(x):
        return html.escape(str(x)) if x is not None else ""
    trs = []
    for r in rows:
        vclass, label, color = classify(r)
        url = r.get("url") or ""
        name = esc(r.get("name") or r["catalog_id"])
        link = f'<a href="{esc(url)}" target="_blank" rel="noopener">{name}</a>' if url else name
        prov_html = (' <span class=prov title="license+hash provenance, not sandbox-run">prov</span>'
                     if vclass == "prov" else "")
        trs.append(
            f'<tr data-status="{esc(r["status"])}" data-vclass="{vclass}" data-market="{esc(r.get("marketplace"))}" '
            f'data-cat="{esc(r.get("category") or "")}" data-prov="{1 if r.get("provisional") else 0}">'
            f'<td>{link}</td><td>{esc(r.get("creator") or "")}</td>'
            f'<td>{esc(r.get("marketplace"))}</td>'
            f'<td><span class="badge" style="background:{color}">{esc(label)}</span>'
            f'{prov_html}</td>'
            f'<td>{esc(r.get("gate_state") or "")}</td>'
            f'<td>{esc(r.get("price_class") or "")}</td>'
            f'<td>{esc(r.get("license") or "")}</td>'
            f'<td>{esc(r.get("category") or "")}</td></tr>')
    markets = "".join(f'<option value="{esc(m)}">{esc(m)} ({n})</option>' for m, n in by_market.most_common())
    page = f"""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Blender Vault Catalog — {total} entries</title><style>
:root{{color-scheme:light dark}} body{{font:14px/1.5 system-ui,sans-serif;margin:0;padding:1rem;max-width:100%}}
h1{{font-size:1.4rem;margin:.2rem 0}} .head{{position:sticky;top:0;background:Canvas;padding:.5rem 0;z-index:2;border-bottom:1px solid #8884}}
.stat{{display:inline-block;margin-right:1rem;font-weight:600}} .big{{font-size:1.6rem;color:#1a7f37}}
input,select{{font:inherit;padding:.3rem;margin:.2rem}} table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{text-align:left;padding:.35rem .5rem;border-bottom:1px solid #8883;vertical-align:top}}
th{{cursor:pointer;position:sticky;top:4.2rem;background:Canvas}} .badge{{color:#fff;padding:.1rem .4rem;border-radius:.3rem;font-size:11px;white-space:nowrap}}
.prov{{font-size:10px;color:#0969da;border:1px solid #0969da;border-radius:.2rem;padding:0 .2rem;margin-left:3px}}
.legend{{font-size:12px;color:#666;margin:.3rem 0}} .note{{font-size:12px;color:#9a6700}}
a{{color:#0969da}} @media(prefers-color-scheme:dark){{a{{color:#58a6ff}}}} #wrap{{overflow-x:auto}}
</style></head><body>
<div class=head><h1>🗂️ Blender Vault Catalog</h1>
<div><span class="stat big">{total} entries</span>
<span class=stat style="color:#1a7f37">✓ {gate_verified} gate-verified</span>
<span class=stat style="color:#0969da">◆ {prov_verified} provenance-verified</span>
<span class=stat style="color:#9a6700">↓ {cta} click-to-get</span>
<span class=stat style="color:#82071e">✕ {excl} excluded</span></div>
<div class=legend><b>gate-verified</b> = sandbox-proven tool (real native-CI pass/partial) ·
<b>provenance-verified</b> = license+hash-proven asset/enumeration, never sandbox-run (<span class=prov>prov</span>) ·
<b>click-to-get</b> = free but checkout/download-gated (owner clicks) · <b>excluded</b> = dead / paid / NC-ND-segregated.</div>
<div class=note>⚠ Known noise: category tags on asset/provenance rows are keyword-derived (from source query/name) — hints, not gate-verified capability tags. Campaign CLOSED at snapshot-catalog-v1; growth via the monthly discovery engine.</div>
<div><input id=q placeholder="filter name/creator/category…" oninput=f()>
<select id=vc onchange=f()><option value="">all verification</option><option value=gate>gate-verified</option><option value=prov>provenance-verified</option><option value=cta>click-to-get</option><option value=excl>excluded</option></select>
<select id=mk onchange=f()><option value="">all marketplaces</option>{markets}</select>
<label><input type=checkbox id=hideprov onchange=f()> hide provisional</label></div></div>
<div id=wrap><table id=t><thead><tr>
<th onclick=s(0)>Name</th><th onclick=s(1)>Creator</th><th onclick=s(2)>Marketplace</th>
<th onclick=s(3)>Verification</th><th onclick=s(4)>Gate</th><th onclick=s(5)>Price</th><th onclick=s(6)>License</th><th onclick=s(7)>Category</th>
</tr></thead><tbody>{''.join(trs)}</tbody></table></div>
<script>
const T=document.getElementById('t'),rows=[...T.tBodies[0].rows];
function f(){{const q=document.getElementById('q').value.toLowerCase(),vc=document.getElementById('vc').value,
mk=document.getElementById('mk').value,hp=document.getElementById('hideprov').checked;
for(const r of rows){{const t=r.textContent.toLowerCase();
r.style.display=(!q||t.includes(q))&&(!vc||r.dataset.vclass==vc)&&(!mk||r.dataset.market==mk)&&(!hp||r.dataset.prov=='0')?'':'none';}}}}
let sd=1;function s(i){{sd=-sd;rows.sort((a,b)=>sd*(a.cells[i].textContent||'').localeCompare(b.cells[i].textContent||''));
const tb=T.tBodies[0];rows.forEach(r=>tb.appendChild(r));}}
</script></body></html>"""
    outdir = ROOT / "reports/catalog"; outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(page)
    # also emit into the served progress/ dir so progress/serve.sh exposes THE LIST (goal face 2)
    served = ROOT / "progress" / "catalog.html"
    if served.parent.exists():
        served.write_text(page)
    print(json.dumps({"total_entries": total, "gate_verified": gate_verified,
                      "provenance_verified": prov_verified, "click_to_get": cta, "excluded": excl,
                      "html": str(outdir / "index.html"), "served": str(served)}))


if __name__ == "__main__":
    main()

# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6", "numpy>=1.26"]
# ///
"""corpus_mcp.py — the Blender Vault MCP server (D-008 R54), the PRIMARY interface any fresh LLM
(Stage 2 included) uses to navigate the corpus. Stdio JSON-RPC (MCP 2024-11-05), dependency-light —
no MCP SDK required. Wraps the same six functions as the CLI twin (corpus_cli.py), so both interfaces
enact one doctrine: RETRIEVAL PROPOSES / THE REGISTRY DISPOSES (R53).

Run:  RAG_EMBED=ollama uv run .archon/mcp/corpus_mcp.py     (or register in an MCP client config)
Tools: search_capabilities · query_registry · get_card · get_usage · find_substitutes · plan_recipe
"""
import json, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import corpus_cli as C

TOOLS = [
    {"name": "search_capabilities",
     "description": "PROPOSE corpus tools for a natural-language need (hybrid RAG). Returns cards to "
                    "consider — NOT a selection. Always follow with query_registry to resolve (R53).",
     "inputSchema": {"type": "object", "properties": {
         "nl": {"type": "string", "description": "the natural-language capability need"},
         "medium": {"type": "string", "enum": ["ground", "water", "air", "organic"]},
         "verb": {"type": "string"}, "near": {"type": "string", "description": "graph node key to constrain near"}},
         "required": ["nl"]}},
    {"name": "query_registry",
     "description": "DISPOSE: deterministic facet query over the authoritative registry (corpus.db). "
                    "Returns ONLY verified, license-tagged, resolvable operators/recipes. Tool selection "
                    "terminates here. recipe_unverified/graveyard are never resolvable.",
     "inputSchema": {"type": "object", "properties": {
         "verb": {"type": "string"}, "medium": {"type": "string"}, "niche": {"type": "string"},
         "quality_min": {"type": "string", "enum": ["asset_fed_minimal", "composed", "full_generator"]},
         "license_class": {"type": "string"}, "blender_ver": {"type": "string"}}}},
    {"name": "get_card", "description": "Tier-1 ~120-word card for an operator/recipe id.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "get_usage", "description": "Tier-2 full manifest (verify states, operators) for an id.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "find_substitutes", "description": "Substitutable operators/recipes for an id or niche (graph walk).",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "plan_recipe", "description": "Composition recipe(s) for a niche; resolvable iff recipe_verified.",
     "inputSchema": {"type": "object", "properties": {"niche": {"type": "string"}}, "required": ["niche"]}},
]


def dispatch(name, args):
    if name == "search_capabilities":
        return C.search_capabilities(args["nl"], args.get("medium"), args.get("verb"), args.get("near"))
    if name == "query_registry":
        return C.query_registry(args.get("verb"), args.get("medium"), args.get("niche"),
                                args.get("quality_min"), args.get("license_class"), args.get("blender_ver"))
    if name == "get_card":
        return C.get_card(args["id"])
    if name == "get_usage":
        return C.get_usage(args["id"])
    if name == "find_substitutes":
        return C.find_substitutes(args["id"])
    if name == "plan_recipe":
        return C.plan_recipe(args["niche"])
    raise ValueError(f"unknown tool {name}")


def reply(rid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n"); sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        m, rid, params = req.get("method"), req.get("id"), req.get("params") or {}
        if m == "initialize":
            reply(rid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                        "serverInfo": {"name": "blender-vault-corpus", "version": "1.0"}})
        elif m == "notifications/initialized":
            continue
        elif m == "tools/list":
            reply(rid, {"tools": TOOLS})
        elif m == "tools/call":
            try:
                out = dispatch(params["name"], params.get("arguments") or {})
                reply(rid, {"content": [{"type": "text", "text": json.dumps(out, indent=1)}]})
            except Exception as e:
                reply(rid, error={"code": -32000, "message": str(e)})
        elif rid is not None:
            reply(rid, error={"code": -32601, "message": f"method not found: {m}"})


if __name__ == "__main__":
    main()

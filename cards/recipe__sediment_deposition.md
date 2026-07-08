# recipe: sediment_deposition
**What it does:** compose petak5__bp::object.create_terrain_operator + petak5__bp::object.erosion_operator → sediment_deposition.
**Verbs:** (composition)  ·  **Media:** ground  ·  **Niches:** sediment_deposition
**Quality:** composed (recipe_unverified)  ·  **License:** license unrecorded — verify before commercial use.
**Steps:** petak5__bp::object.create_terrain_operator ; petak5__bp::object.erosion_operator
**Also known as:** —
**Example:** run .archon/scripts/verify_recipes.py --versions 4.5
**Note:** petak5 create_terrain drives (delta); erosion_operator is modal-noop headless. create_terrain alone makes terrain not se
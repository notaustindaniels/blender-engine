# Taxonomy Proposals (§12.1(6))

Harvested add-ons that survived verification but map to NO **wave-1 Terrain+Veg** niche — candidate
wave-2/3 mappings or new niches. **Owner-approved only; never auto-added** (R40, D-006). These batch
into the next consolidated owner session; none affects the gate-v2 (wave-1 T+V) numerator until the
owner rules.

## Batched for the consolidated owner session

- **`tu2463__rock_generator_addon`** — operator `mesh.primitive_rock_add`, **FULL PASS on 3.6 / 4.2 / 4.5**
  (render_ok all three). Not mapped by enrichment because it targets wave-1 T+V, but it is a strong
  semantic match for the **existing wave-2 niche `rock_boulder_generator`** ("procedural individual
  rocks", verbs `[generate]`, taxonomy line 281).
  - **Proposed disposition (owner decides):** map `mesh.primitive_rock_add → rock_boulder_generator`
    (wave-2). This is **off the wave-1 gate**, so it does not move gate-v2 now — it records real
    Stage-2 capability (a verified free procedural rock generator).
  - **Alternative:** if the owner considers `rock_boulder_generator` too narrow, keep as an unmapped
    wave-3 candidate. **Default = no change until owner approval** (R40).

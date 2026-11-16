# Initial sketch pointer clears do not prove null caches

Expected: the first stores clearing sketch runtime `+0x550/+0x558` in its constructor describe the final fresh helper state.

Actual: in pinned SOLIDWORKS 2026 model image SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, complete sketch constructor `[0x4c495450,0x4c49645e)`, SHA `5b351f5b063df2246cd9d98eba252efb5da24ba545d7fb8b2891af5e6b9cf8eb`, clears the pointers at `0x4c4960a7/0x4c4960ae`, then constructs and stores separate helper objects at `0x4c4961a9/0x4c4961d4`. Successful fresh allocation therefore normally yields a `moPointToEntitiesSketchMap_c` and `moEntityToDimsSketchMap_c`, not two null pointers. The later stores must be included.

The first helper starts dirty and can rebuild incident-entity roles. The second starts with its own dirty flag one; the selected fresh constraint-append notification returns while that flag remains set. These are different concrete receivers and different predicates. A null-branch proof for one cannot be transferred to the other.

Workaround: retain the entire constructor extent and trace the final value of each pointer into the actual consumer. For the generic circle-center fix, cover cached point-role lookup and the fresh entity-to-dimension-map notification explicitly. Do not add runtime cache pointers or captured map rows to writer output. Constructor allocation facts do not prove arbitrary later cache contents, numerical solver behavior or native acceptance.

Evidence: [native identities and extents](../../../../../re/solidworks/records/CircleCenterFixation2026.json), [bounded construction and remaining conditions](../../../../../re/solidworks/records/CircleCenterFixation2026.md). Only independently authored facts and hashes are recorded; proprietary listings remain outside the repository.

# Constructor prefix is not final state

## Expectation

The first zero stores in the downstream constructor establish the final prefix and timestamp defaults.

## Actual behavior

In the pinned 2026 `moDownstreamIdData_c` constructor, the tail overwrites `f0c` with the current native file-version getter, `f10` with `su_getFullDateCode()`, `f1c/f20` with `101`, and runtime i64 `f28` with `su_CTime(1990,1,1,0,0,0,-1)`. It also replaces the initially null model-owner member. `f08` remains one and `f14/f18` remain zero. An initial-store-only interpretation is refuted by those later instructions.

The time constructor uses local calendar semantics. Runtime width also differs from the proven four-byte ordinary archive encoding. Neither a captured epoch nor an eight-byte wire timestamp follows from these stores.

## Workaround

Read the complete constructor, including all chained extents, and track overwrites before recording final field rules. Keep those constructor rules separate from post-update or saved state. Bind imported producer semantics before replacing a getter with a generated value. Preserve runtime/wire width distinctions.

The [source-pinned record](../../../../../../re/solidworks/records/DownstreamConstructorEnable2026.md) provides final assignments, import identities, full bounds and remaining limits. No populated-state writer, standalone save route or native acceptance is established by this correction.

# Sketch backlinks depend on archive context

A constructed sketch retains its actual profile at `f138`.
That runtime relationship does not imply a stored backlink in every archive mode.
The current sketch grammar emits `f138` only when archive context `ctx874` is nonzero.
The ordinary linked Config/Resolved profile uses the default zero context.
Its decoded sketch therefore has no `f138` field.

The first separate polygon preparation failed with `KeyError: 'f138'` after both generated builds passed.
The checker had assumed the constructor backlink was serialized in this ordinary mode.
The feature constructor's `owner` field is also runtime metadata on this path.
The generic SDK codec preserves wire fields and does not recreate vendor post-load runtime links.

Keep the construction-time backlink check.
During ordinary linked readback, verify the stored profile `pd_f80` reference against the actual mapped sketch object.
Verify the model through the profile's `pd_f78` component-plane wrapper, its `f58` unit component and that component's serialized `owner` reference.
Retain the extrusion's actual profile dependency and inherited Config map aliases.
Do not add a fabricated backlink or change archive context to satisfy a checker.

The [construction ledger](../../../../../../re/solidworks/records/SdkPolygonConstruction2026.md) records the failed source and narrow correction.
The [profile ledger](../../../../../../re/solidworks/records/ProfileConstruction2026.md#verification)
also distinguishes the separate sketch-info test that explicitly selects `ctx874=1`.
That mode's backlink assertion does not apply to ordinary linked streams.

Both corrected four- and seven-sided process flows pass their actual serialized ownership checks.
The [sanitized receipt](../../../../../../re/solidworks/measurements/2026/SdkPolygonConstruction01.json) binds the frozen source and outcomes.

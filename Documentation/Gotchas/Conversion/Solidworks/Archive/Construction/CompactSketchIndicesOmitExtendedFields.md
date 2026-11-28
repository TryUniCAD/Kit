# Compact sketch indices omit extended fields

Constructed sketch handles retain their full semantic index in `f18`.
The wire stores that field only when `idx` equals the `0x777f` escape marker.
Below the marker, the SDK graph contains the compact `idx` field alone.
Segment endpoints use the same distinction with marker `0xffff`.
Their compact fields are `fc8_s/fcc_s`; their conditional extensions are `fc8/fcc`.

The second polygon preparation failed with `KeyError: 'f18'` after its serialized ownership checks passed.
The checker expected a full runtime index beside every compact wire index.
The SDK decoder correctly retained only the fields present in that wire branch.

Resolve the semantic index from the selected wire branch.
Below the marker, require the compact value to equal the actual target index and require the extension field to be absent.
At the marker, require the extension field and validate its full index against the actual ordered target.
For a generated canonical index, the full value must be at least the marker.
Do not add synthetic runtime fields to a raw decoded graph to satisfy a checker.

The [polygon ledger](../../../../../../re/solidworks/records/PolygonConstruction2026.md#independent-namespaces-and-topology)
binds both marker rules to their native serializers.
The [SDK construction ledger](../../../../../../re/solidworks/records/SdkPolygonConstruction2026.md)
records the failed check, conditional-field audit and corrected process scope.

Both corrected four- and seven-sided process flows pass with compact indices.
The [sanitized receipt](../../../../../../re/solidworks/measurements/2026/SdkPolygonConstruction01.json) records the observed branch counts.
These cases provide no new execution evidence for extended-width indices.

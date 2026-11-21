# Profile displays can reference child origins

An exact concrete `moProfileFeature_c` filter can miss a valid drawing profile target. In both disclosed original drawings the wrapper's persistent ID selects the actual linked `moOriginProfileFeature_c`; the ordinary `Sketch1` feature has a different ID.

The pinned native getter uses `IsKindOf(moProfileFeature_c)`, and the origin's actual RTTI includes that base. Resolve the actual component/file/configuration and persistent feature ID, admit only independently verified concrete subclasses, and validate creation time. Preserve the origin role. Do not select the ordinary sketch by name or shift the stored ID.

The corrected observer finds one matching origin in both original and saved states. Earlier exact-class-only metadata remains retained. [Native proof and process evidence](../../../../../../re/solidworks/records/DrawingOriginProfileLinkage2026.md).

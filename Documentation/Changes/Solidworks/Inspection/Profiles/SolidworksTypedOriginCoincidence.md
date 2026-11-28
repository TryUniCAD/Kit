# Typed origin-coincidence rectangle reads

The public SOLIDWORKS reader preserves a qualified ordinary origin-anchored rectangle as four actual contour lines, one fixed external construction datum and seven owned relations. The origin datum follows its actual model/profile reference chain. Its type-9 coincidence, horizontal/vertical rules and two driving lengths retain actual native IDs, endpoint selections, parameter owners and provenance.

Native-saved line arrays may retain a deleted first row. That row and the actual optional region cache are preserved as metadata while line, relation and boundary handles keep their original array namespace. Unsupported external ownership, support frames, extra relations or incomplete boundaries keep the earlier legacy projection without a typed origin claim. Creation-log freshness is explicitly unvalidated.

Usage is the existing `convert.open_document` or strict CLI decode path; there is no new option or writer registration. This does not admit the full f14a FCStd source or other rectangle anchoring modes.

Verification uses a frozen 5,813-path SDK source closure, 26 guarded deterministic builds and 54 public read calls across seven integration cohorts. Seven additional strict normal-document reads cover the generated original, all three disclosed native corner files and all three actual native-saved generated edits. Those seven files also round-trip Config and linked Resolved exactly in guarded processes. All inputs stay unchanged. The scoped static checks and donor scan pass.

[Field and scope record](../../../../../re/solidworks/records/SdkOriginCoincidenceRead2026.md) · [Process receipt](../../../../../re/solidworks/measurements/2026/SdkOriginCoincidenceRead01.json) · [Handle-domain gotcha](../../../../Gotchas/Conversion/Solidworks/Tracing/Sketches/NativeSketchHandleIndices.md)

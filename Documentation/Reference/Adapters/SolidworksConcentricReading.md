# Read ordinary concentric mates

Use the normal `convert.open_document(path)` entry point for the measured ordinary SOLIDWORKS 2026 assembly profile. Require `document.metadata["solidworks.typed_mates_semantics"]["status"] == "admitted"` and `full_selected_mate_graph == True` before treating its concentric selections as complete typed semantics.

The admitted profile has one solved concentric mate, two rigid direct occurrences of one saved cylinder part/configuration and one fixed occurrence. The ordinary aligned and anti-aligned modes and both rotation-lock states are read. The child must contain the actual saved single-cylinder kernel body and its profile/extrusion owners.

The mate entities have `kind == "cylinder"`, a radius in millimetres, their actual instance paths and a source face ID present in the resolved child B-rep. `MateConstraint.alignment` retains aligned or anti-aligned intent. Its `attributes["rotation_locked"]` retains the actual Boolean lock choice. The instance `fixed` flags and selected configuration names come from the native owners.

The entity frame remains absent. Actual stored world points in metres and unit axes are available as `stored_origin_m` and `stored_axis` attributes. No unproved reference-direction convention is introduced.

Set `include_brep=False` and `include_tessellation=False` for metadata-only output. No child B-rep is returned; the verified mate identity still addresses the saved child face. Source face IDs are document-specific wire identities and can change after a native edit. The separate native face-node and body-atom IDs remain available for audit, rather than being confused with a neutral face-array position.

Disabling `resolve_components` through `ReadOptions.values` preserves the existing legacy read behavior. Unsupported or contradictory profiles retain a precise unsupported typed status where the narrow route is attempted. Do not qualify their complete mate semantics from the legacy face text.

Mixed concentric/planar groups, multiple concentric mates, nested or flexible references, alternate configurations, missing saved kernel ownership, reference axes/edges and misaligned/linked positions remain outside this route. Public concentric generation is not enabled.

The host proof covers six disclosed native saves in both read modes, twenty-two malformed cases, all four existing planar families and disabled component resolution. No new native run or held-out qualification is claimed. [Evidence and limits](../../../re/solidworks/records/PublicConcentricMateRead2026.md) · [Change entry](../../Changes/Solidworks/Reading/Mates/SolidworksPublicConcentricReading.md)

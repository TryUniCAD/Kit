# RTTI class names can differ from archive tags

Expected: a concrete type's name in the serializer/vtable map is also the name written into the ordinary object archive.

Actual: pinned SOLIDWORKS 2026 constructs `moConstraintDefaultPlaneRefplaneData_c`, but that concrete vtable inherits the same `GetRuntimeClass` accessor as `moConstraintRefplaneData_c`. It returns the base class's descriptor/name. The ordinary `su_CArchive::WriteObject` path calls that accessor before `WriteClass`. The distance geometry has its own matching runtime name, so this is a specific publication rule rather than a blanket class-name rewrite.

Workaround: trace the concrete constructor and its actual runtime-class descriptor separately. Register the published archive name with its proved field order; retain the concrete RTTI name as construction evidence. Do not create a wire alias from saved bytes, infer the name from a shared serializer alone, or change the serializer-map generator's interface to hide the distinction.

[Exact module identities, numeric rule and reproducible receipt](../../../../../../re/solidworks/records/ReferencePlaneRuntimePublication2026.md). The first source-audit preparation was corrected from original binary evidence before any source model read. This rule does not establish source or generated native acceptance.

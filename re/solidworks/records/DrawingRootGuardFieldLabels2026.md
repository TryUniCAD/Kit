# Drawing guard observation field-label correction

The archived generic root observer labels every integer `f08` as `persistent_id`. That semantic label is wrong for its `moEdgeRef_c` entries: the inherited `moBEntRef_c.f08` is the entity-reference count, not a feature ID. The immutable tool and original report are retained unchanged; this separate correction supplies the actual owner.

Task: PR121 drawing root-guard metadata correction. Owner: `flag_ownership`; delivery PR: #121. Dependency: the actual root-state observation and independently verified reference body. Exit: exact report/source custody plus the correct class-specific field meaning. This changes no SDK grammar, writer, source CAD file or acceptance verdict.

The complete native `moBEntRef_c::setLocalFeatureToNULL` closure is `[0x4b759a30,0x4b759a86)`, three chained fragments, 86 bytes, combined SHA-256 `c842fe8c8e234255b836de45d1243a3935d0584ebb8d8e1e9906ca24b76dae27`, in original `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The count at runtime `+0x08` bounds its 16-byte entity array at `+0x10`. The shared [resolved reference layout](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ReferenceFields.py) independently names the unsigned32 wire `f08` and the repeated `f10` entities.

The [exact correction metadata](DrawingRootGuardFieldLabels2026.json) binds original observer SHA-256 `24af0a2e00a92ff3f3aebda328436056d3fc41731ce49996751d36f374e681cc`, root report `89063a943ff99b9ece6b4efc811e96c534ada9119dcd39e25b3b28284b5a69b7`, and the new independently executed typed process `a019d6731d635e266084b2d85a5474722721ad6c1f969bf61f6ea1c32e0a3c81`. Each reported edge's historical numeric value matches the newly labeled actual entity count. No implementation default is drawn from those values.

Keep node persistent IDs, kernel downstream IDs and entity-array counts distinct. An offset shared by unrelated classes is not a semantic field identity. [Specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/FieldOffsetsNeedTheirConcreteOwner.md).

The governing stopping conditions remain: “The first is success under every criterion on this page.” and “The second is the end of the available context.” No native or held-out qualification is added.

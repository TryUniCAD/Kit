# Drawing runtime owners follow serialized containment

## Expectation

Every feature's runtime `owner` backlink appears as a separate archive field and is present immediately after the shared body reader finishes.

## Actual behavior

The generated model carries runtime feature owners. The qualified drawing body layouts serialize the ordered concept child lists and actual reference-manager paths, without a separate general feature-owner word. A freshly read sheet, view or support feature therefore lacks that runtime member. Treating its absence as a wire mismatch rejects an otherwise byte-identical complete read.

The one-view SDK proof first reached this boundary after its candidate had already matched the entire independent Definition. Reconstructing ownership from actual containment preserves the complete read/re-emission bytes and native object map. A runtime sketch/profile backlink has the same separate construction-versus-persistence distinction.

## Correct use

After a complete linked read, bind the model's owned children, the sheet's children and the view's ordered supports to their actual containing objects. Bind the internal reference and the property-manager reference to the actual drawing model. Reject conflicting existing backlinks. Continue to validate serialized aliases independently, including the active sheet, support planes, shared child directory and external-reference backlink.

Do not append invented owner words to the stream or substitute matching persistent IDs for actual graph identity. The [linked Definition ledger](../../../../../../re/solidworks/records/DrawingLinkedDefinition2026.md) and [thirty-process receipt](../../../../../../re/solidworks/measurements/2026/SdkDrawingFrontDefinition01.json) record the bounded proof. The broader native conversion criteria remain open.

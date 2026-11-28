# Derive relative addresses from the pinned image

## Expected

An earlier construction record's image base can be combined with its absolute
function addresses to calculate native hook RVAs.

## Actual behavior

The profile ledger listed `sldmfcu.dll` base `0x3c800000`. The pinned 2026 PE
header specifies `0x3c720000`. Its line-width constructor really is at absolute
address `0x3c84a8f0`, giving RVA `0x12a8f0`, not `0x4a8f0`.

Direct 2026 inspection reverified the model's import of that constructor and its
width/category rules. The function address and rules were correct; the recorded
base was not. Treating all three as one unexamined fact would create an invalid
hook target while appearing to preserve the earlier address.

## Workaround

Bind every preferred base to the exact PE header and binary hash. Resolve the
owning import/export and verify the actual function before computing its RVA.
Use the observed runtime module base only after that calculation. Correct a
record's bad base without assuming that its function addresses or field rules
must also change.

The [constructor evidence](../../../../../re/solidworks/v2026/evidence/LineWidthConstructor2026.json)
records both image hashes, import slot, absolute address, correct RVA and checked
constructor rule. No CAD process or saved document was used for that check.

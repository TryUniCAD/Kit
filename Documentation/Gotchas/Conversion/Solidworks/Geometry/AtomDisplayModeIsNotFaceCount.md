# Atom display mode is not face count

Expectation: a `moAtom_c.f19c` value of six in a six-face rectangle might encode the number of faces.

Actual behavior: the exact SP05.2 atom constructor seeds that field to six before a body exists. The exported `moAtom_c::setDisplayMode` at `[0x4b292070,0x4b292077)` writes its integer argument to `this+0x19c`. Its original-byte SHA-256 is `0e96150157ce8029972e1f7b7ee1796a1623c8c6088cb87c70fd77fcc8d51c60`; the module is `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

Workaround: derive topology counts from the complete body/shell/face graph. Treat this atom field as constructor display state, with other modes outside the qualified profile. A prior research comparison's equality to a rectangle's face count is coincidental and is not used by the typed public name reader or cold constructor.

See [the ownership record](../../../../../re/solidworks/records/NamedBodyOwnership2026.md), [the reader boundary](../../../../../re/solidworks/records/SdkNamedBodyRead2026.md) and [the cold construction rule](../../../../../re/solidworks/records/NamedBodyColdReuse2026.md).

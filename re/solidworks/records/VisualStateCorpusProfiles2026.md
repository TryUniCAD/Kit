# SOLIDWORKS 2026 VisualStates corpus profiles

Task `B04-SW2026/VISUAL-STATE-CORPUS` is owned by the PR #121 takeover.
Its exit is complete typed stream replay on the 88 disclosed 2026
part and assembly files. Native construction and document acceptance
remain separate.

The stream starts a local map at 1 under archive conditions
`0x20004000`. Each measured file carries archive version 19000 and
schema-one `visStateKeyData_c`. All 88 embedded tracker lists are empty.
The part self holder occurs in 80 files. Six assemblies reach nine
detached external features through display-state context chains.
[Existing typed graph census](BinaryArchiveCorpus2026.md)

| Owner | Version-19000 evidence and typed scope |
| --- | --- |
| Displayed entity tracker | The actual `sldvisualstateu` key-data loader at `0x3273ff50` calls the explicit `moDisplayedEntityTracker_c::Serialize` helper once its effective version exceeds `0x1100`. This is distinct from the class's virtual zero-wire base serializer. In `sldmodu` at `0x4be70580`, the store writes the map size as a signed long at `0x4be705cf`, then a CString key and an object per entry at `0x4be70606` and `0x4be70617`. The load reads the signed count at `0x4be70696`, repeats while it is positive, and reads key then object at `0x4be706c2` and `0x4be706d3`. The profile proves its zero-row path only. Populated trackers and negative wire counts remain outside its qualified domain. |
| Part self holder | `moCompHolder_c` uses the inherited `moCompRef_c::Serialize` slot at `0x4bba67d0`. The archive reads the actual part unit component into `f58` and then the inherited fields. The measured holder has no optional old reference, faceted data, locator, component info, transform or extra string payload. Other versions, owner classes and populated optional fields retain provisional classification. |
| Detached assembly feature | The actual schema-one reference appears inside a VisualStates context chain's external feature list. The detached path retains the shared file identity and actual CString name handle, unset configuration selector, clear flags and the absent backlink. The original Config and CMgr reference profiles keep their existing admission rules. Other archive flags and contexts retain provisional classification. |

The exact case profiles are in [Visual.py](../../tooling/sw2026/serial/defs/Visual.py)
and [VisualRefs.py](../../tooling/sw2026/serial/defs/VisualRefs.py).
The verified serializer map records the holder slot independently of
the tracker helper. The [module manifest](../v2026/Manifest2026.json)
binds both native DLLs to SOLIDWORKS `34.5.2.0604`.
The local previous Ghidra exports used to verify the calls have
SHA-256 `db513674329b8fd6f981bf9c5a1a62b951596a48031d23d148cb0241685ba3ec`
for the model module and
`69f879010a6bb747b20171c6e3d9c6f3a76210e884459d8a1339b92eafa67fce`
for the display-state module. The exports remain outside the checkout.
[Serializer map](../../data/Serialization/SerializeMap2026.json)
[Native external reference wire](ExternalReferenceWire2026.md)

All 1,328 streams in the complete disclosed binary audit replay byte
for byte without opaque data, unread tails, missing or provisional
schemas. Only the 88 VisualStates qualification rows changed from the
previous full report. Each source identity, byte length, stream digest
and map counter remained equal. The other 1,240 stream results are
identical. [Integrated receipt](../measurements/2026/BinaryArchiveAfterVisualProfiles01.json)

# SOLIDWORKS 2026 configuration manager header construction

`Contents/CMgrHdr2` is the lightweight directory of saved configurations. A
referencing assembly can read the child's manager save timestamp from this
stream. The part constructor takes the generated full configuration manager
and an explicit manager save event, then builds the lightweight projection.
See the directory and occurrence timestamp paths in
[AssemblyConstruction2026.md](AssemblyConstruction2026.md#child-directory-timestamp-sources).

## Build and archive layout

The trace uses SOLIDWORKS 2026 SP05.2, `sldworks.exe` build `34.5.2.0604`,
archive version `19000`. Addresses are preferred virtual addresses for the
following installed x64 modules. REA's PE resource inspection identified
`doccplu.dll` and `sldarchiveu.dll`. LLVM PE disassembly supplied constructor,
accessor, vtable and call-site evidence.

| Module | SHA-256 |
| --- | --- |
| `doccplu.dll` | `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8` |
| `sldarchiveu.dll` | `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48` |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |

`doccplu.dll!SolidStorage_c::SaveConfigMgr` at `0x18003e000` calls
`dmConfigMgrHeader_c::addConfigHeader` at `0x18003ee5f` and stores the
constructed header at `0x18003efb2`. In `sldarchiveu.dll`, `addConfigHeader`
at `0x319f7920` forwards the arguments to the `dmConfigHeader_c` constructor
at `0x319f7a13`, then appends the new object to the embedded list at
`0x319f7a26`. Its constructor is at `0x319f58c0`. The manager's own constructor
at `0x319f5a80` initializes the embedded list. Runtime descriptors at
`0x31a24090` and `0x31a240c0` hold schema `0x80000001` at `+0x0c`, giving
wire schema `1` for both concrete types.

The [existing schema](../../tooling/sw2026/serial/defs/SmallHeader.py) uses
one rooted `dmConfigMgrHeader_c` with a new map at base `1`. The archive
serializer computes class tags, list counts and object entries. The embedded
list contributes a normal `suObList` count and child objects. Its manager
and child store implementations are `0x319f7270` and `0x319f6d90` in
`sldarchiveu.dll`. At version `19000` the legacy manager list at `+0x58` is
absent. The child constructor's transient `+0x3c`, `+0x58`, `+0x60`, `+0x64`,
`+0x68` and `+0x70` have no fields on this store path.

## Emitted values

`SaveConfigMgr` obtains the configuration list at `0x18003ea66`. It skips
configurations with nonzero `+0xbf0` at `0x18003eba8` or a nonzero
`getPurgeConfigOnSave()` result at `0x18003ebb9`. The latter accessor
`sldmodu.dll!0x4b288af0` reads `+0xbe0`. The fresh base configuration
constructor at `0x4bdbf820` clears both fields at `0x4bdbfe5c` and
`0x4bdbfe7f`. The builder takes one independent configuration that belongs to
the part and is selected by both manager pointers, covering the ordinary
active-selection path. It rejects excluded state or a feature-comment
sidecar when present in the input graph.

| Manager field | Wire type | Classification and rule | Native evidence |
| --- | --- | --- | --- |
| `f08` | Embedded `suObList` | Derived list of the visited applicable configurations. Its count comes from the generated entries. | `doccplu.dll!0x18003ea66` and `sldarchiveu.dll!0x319f7a26` |
| `f60` | `time32` | Input manager save timestamp in Unix seconds. | `doccplu.dll!0x18003ea95` to `0x18003eaa5`; `sldmodu.dll!0x4b2875f0` reads the manager at `+0x570` |
| `f68` | `i32` | Derived from the manager's tree sort order `f75c`, keeping all 32 bits. | `doccplu.dll!0x18003eaad` to `0x18003eabc`; `sldmodu.dll!0x4b2850f0` reads `+0x75c` |

Each row below is in `dmConfigHeader_c` version `19000` store order. Unless
otherwise qualified, the caller addresses belong to `doccplu.dll` and the
getter addresses belong to `sldmodu.dll`.

| Configuration field | Wire type | Classification and rule | Native evidence |
| --- | --- | --- | --- |
| `f08` | `i32` | Derived active selection. The visited object equals the selected configuration, yielding `1` in this scope. | Selection at `0x18003ea6b` to `0x18003ea82`; identity comparison at `0x18003ec4a` |
| `f10` | `CString` | Derived name from the actual configuration node's `f18.f08`. | `0x18003edad` calls `getName` at `0x4b287de0`; slot `+0x88` dispatches to `0x4bb4d460` and node `name()` |
| `f30` | `i32` | Derived from the actual configuration's ID `f08`. | `0x18003ed7b`, virtual `+0x188` resolves to `0x4b283ba0` |
| `f38` | `u32` | Derived from the actual configuration update stamp `f860`. | `0x18003ebd1` |
| `f18` | `CString` | Derived feature description. Uses `f1f8` when present and the node name when empty, for the ordinary generated graph without a Description custom-property override. | `0x18003ed9c` calls virtual `+0x16b0` at `0x4bdd8490`; the ordinary path invokes `0x4bb42ce0` with argument `0` |
| `f34` | `i32` | Derived from the parent object. A null parent gives the native `-1` sentinel. | `0x18003ed43` calls `0x4b286f90` for `+0x6a0`; branch at `0x18003ed6a` |
| `f40` | `i32` | Derived rebuild status. It is `1` if `f968 != 1` and `f0c & 8` is set, and `0` otherwise. | Call at `0x18003ed34`, implementation `0x4bde3f50` |
| `f20` | `CString` | Derived configuration comment from `f4a8` when the feature-comment list is absent. | `0x18003ed24` calls `0x4bdd71a0`; the empty feature-comment list path uses `+0x4a8` |
| `f28` | `CString` | Derived alternate name `f498`. | `0x18003ed0c` calls `0x4b283980`, which reads `+0x498` |
| `f44` | `i32` | Derived configuration flags `f4c4` with the same 32-bit pattern. | Direct load at `0x18003ecf3` |
| `f48` | `i32` | Derived LDR-DL state `fbd0`. | `0x18003ece7` calls `0x4b287390`, which reads `+0xbd0` |
| `f50` | `u32` | Derived geometry stamp `f1300` from the opened part owner. | `0x18003ec14` calls virtual `+0x19e0`, which resolves to the opened-part getter at `0x4b5602e0` |
| `f4c` | `u32` | Constant `101` for an opened ordinary part. | `0x18003ec23` calls virtual `+0x19d8`, which resolves to the opened-part getter at `0x4b55ff30` |

The active constructor receives the comment at caller stack `+0x48` and the
alternate name at `+0x50` before the call at `0x18003ee5f`. The wrapper
forwards them in that order. Its constructor stores the first string at
`+0x20` and the second at `+0x28` at `0x319f5916` and `0x319f5926`.
The description comes from the separate virtual call and becomes `+0x18`.

The opened-model wrapper `0x4b285780` dispatches virtual `+0x1280`. The part
configuration uses the feature owner getter at `0x4bb45da0`, connecting the
geometry and transform paths to the actual constructed part. The opened
assembly overrides use `0x4b55ff40` for geometry and `0x4b55fdd0` for transforms.
They visit the assembly graph and require their own derivation before extending
this builder to assembly manager headers.

## Construction and evidence

[`ConfigurationHeader.py`](../../tooling/sw2026/builders/ConfigurationHeader.py)
uses existing `Obj`, `object_list` and rooted stream storage to project the
live generated manager. Its inputs supply all authored strings and save
events. Native constructor rules supply the missing-parent sentinel and
part transform stamp. There are no file inputs to either entry point.

The synchronized A12–A14 discovery run contains three parents and two parts.
The `SourceParser/Assembly/Synchronized.json` member of the [discovery artifact](https://github.com/TryUniCAD/Kit/actions/runs/44020546348/artifacts/14301441151)
has SHA-256 `a01a451ffc712efbd2dcbebd042d4e51387d8645e3b1cbab64159a1318f97f03`.
All five manager headers round-tripped exactly within the 40 successful
stream comparisons. The eight directory timestamp comparisons agreed with
the children's separate self-record and manager save event values. Both child
part headers had configuration stamp `134`, transform stamp `101` and
geometry stamp `104`. These observations corroborate source tracing. The
builder computes the stamps using the generated model and native getters.
The A15 and A16 payloads remain sealed. Generated native open, rebuild and
fresh-process edit acceptance for this stream remains pending.

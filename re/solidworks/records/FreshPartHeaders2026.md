# Fresh ordinary SOLIDWORKS 2026 part headers

| Item | Scope |
| --- | --- |
| Task | `B04-SW2026-FRESH-PART-HEADERS` |
| Owner | PR #121 takeover team |
| Delivery | Local `codex/solidworks-fresh-part-headers` on accepted `dade4abef73c4e2a59b2d77371db0f77bf014fa1` |
| Dependencies | #175 standalone Header, #178 CMgrHdr2 and #188 direct ModelHeader pointer binding |
| Exit | Independent authored bytes, complete disclosed stream parity, map ownership, refusals and current-revision review and queue evidence |

## Construction and archive ownership

[`MakePartHeads`](../../../src/convert/adapters/solidworks/Archive/Construction/Header/MakePartHeads.py)
returns the model header, the top-level header and the lightweight
configuration directory for an ordinary part. It takes the actual part
and manager nodes, the live persistent-ID allocator, explicit
creation, modification, update and save events, and a Windows part
locator. The manager's two selectors must alias the same sole
independent configuration row owned by the part. A second manager
row, a derived configuration, excluded state and comment sidecars
are explicit refusals. Multi-configuration construction remains a
separate part composer requirement.

| Owner | Source of emitted values |
| --- | --- |
| `moHeader_c` | The allocator's actual next ID, the declared times and Header role. A one-event log's ID and caption come from the allocated model. Author, company and comment are explicit Unicode text. |
| Standalone `f38` | One shared `moExtObject_c` graph in the two in-memory headers. The file handles come from the part name and supplied locator. The self creation identity uses the model Header's creation event. The save event and selected configuration name and local ID stay distinct. |
| `dmConfigMgrHeader_c` | The one actual selected configuration yields the row. The manager supplies sort order and the caller supplies its save event. |
| `dmConfigHeader_c` | The selected configuration supplies name, ID, comment, alternate name, description, flags, update stamp and load state. The actual owner supplies the geometry stamp. The opened-part constructor supplies transform stamp 101. |

The historical [native-qualified part revision](https://github.com/TryUniCAD/Kit/commit/81aff00e947ef3bb39fb479c265782d7ca7a0581)
supplies the fresh constructor and field rules. This extraction adds a
single part-only composition boundary. File identity excludes assembly
and drawing roots. It validates the root's actual allocation, reuses
the accepted manager descriptors and checks the embedded row shape and
authored text. The accepted Header, CMgrHdr2, map and container codecs
provide all byte emission.

The three ordinary version-19000 streams each start a map at one.
The two Headers have separate revision-list nodes and explicitly
distinct `fec` roles in the fresh recipe. Each reads its own self
object at standalone slot 13 in the authored cases. The direct
ModelHeader handoff can bind its actual self node after the part class
and root at configuration slots 1 and 2. In that map the self object
occupies slot 3 and the inherited base and counter reach 4 without
emitting a tag. The manager's independent map ends at 5. The probe
observes this direct map operation without emitting `Config-0`.

[Header construction rules](https://github.com/TryUniCAD/Kit/blob/ed2928db557adfdaec8cbb1b400d8e51ca2e9d22/re/solidworks/records/MetadataConstruction2026.md)
· [Native manager getters](https://github.com/TryUniCAD/Kit/blob/ed2928db557adfdaec8cbb1b400d8e51ca2e9d22/re/solidworks/records/ConfigurationManagerHeader2026.md)
· [Direct map ownership](ConfigHeaderLinkSlice2026.md)
· [Saved Header roles](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/StandaloneHeaderRolesCanMatch.md)

## Bound process observations

The [numeric receipt](../measurements/2026/FreshPartHeaders01.json)
binds all source and verification paths and the observed outputs.
`straight`, `unicode` and `reserved-tail` construct their own inputs after the
external-access guard. An independent wire author frames the archive
class declarations, class reuses, counts, typed text and owner words
from the declared inputs using `struct`. All nine streams match those
bytes. Readback verifies both actual standalone owner lists, the
manager's four entries, exact re-emission and untouched modeled input.
The cases contrast reserved ID allocation, independent epochs and
text, description fallback, signed manager state and rebuild status.
The trailing-reservation case reserves 8 and 9 after allocating 7.
Both Header counters store 10 and the immediately following allocation
returns 10. The manager directory bytes remain exact.
Reserving the final signed ID refuses Header construction before any
header bytes are emitted.

The native reference scope is SOLIDWORKS 2026 SP05.2
`34.5.2.0604`. The two separately run control readers verify the
tracked fixture hashes before decoding. All six original stream
digests and indexes agree with the accepted Header and CMgrHdr2
observations. L1 is native-authored. ConcaveOwned is a generated
fixture with prior native observations. L1 has equal standalone
Header digests. ConcaveOwned has different digests. Neither fixture
feeds the constructor. Twelve authored invalid owner and input
cases refuse before yielding a header graph.

```sh
python3.14 -I -B re/tooling/sw2026/CheckFreshHeads.py straight
python3.14 -I -B re/tooling/sw2026/CheckFreshHeads.py unicode
python3.14 -I -B re/tooling/sw2026/CheckFreshHeads.py reserved-tail
python3.14 -I -B re/tooling/sw2026/CheckFreshHeads.py ladder
python3.14 -I -B re/tooling/sw2026/CheckFreshHeads.py concave
python3.14 -I -B re/tooling/sw2026/CheckFreshHeads.py refusals
```

The process commands observe internal stream boundaries. The
[`kit research` workflow](../../../Documentation/Tasks/ResearchCommandLine.md)
handles pinned whole-document decode and its qualification metadata.
The internal stream observations leave that qualification intact.

The allocator initialization repair at
`4934ebb439bdcab3beb4fe13daf59bf42245cd37` repeated all nine guarded
processes. The three neutral models, nine generated streams, six
disclosed streams and all twelve refusals match the original observations
exactly. The current source manifest covers the repaired allocator and
canonical part suffix. Runtime external accesses remain zero.
[Revision-bound allocator receipt](../measurements/2026/FreshPartHeadersAllocator02.json)

The queue's Pyright rule requires superclass initialization. Revision
`3bdeae46811e2af2136e6267e29b827a64c61404` restores that call and reads a
previously allocated ID in the existing ownership check. The allocator
passes the scoped steering limit. All nine guarded processes reproduced
the original observations, including the reservation boundary, with
zero external accesses.
[Current allocator receipt](../measurements/2026/FreshPartHeadersAllocator03.json)

## Remaining scope

The public line-boss baseline bound the same construction family
to four guarded SDK calls matching two candidates and a six-process
native lifecycle at the earlier revision. Those results give
historical scope and format evidence. This delivery adds zero
native runs, held-out cases or FCStd conversions.
The integrated part composer still needs the complete Config/Resolved
map handoff, full CMgr, Definition and other required streams.
Complete neutral source preparation, staged publication and
native qualification require the actual combined writer.
[Native lifecycle](https://github.com/TryUniCAD/Kit/blob/ed2928db557adfdaec8cbb1b400d8e51ca2e9d22/re/solidworks/measurements/2026/SdkDefaultPartNative01.json)
· [Public same-byte receipt](https://github.com/TryUniCAD/Kit/blob/ed2928db557adfdaec8cbb1b400d8e51ca2e9d22/re/solidworks/measurements/2026/SdkPublicPartWriter01.json)

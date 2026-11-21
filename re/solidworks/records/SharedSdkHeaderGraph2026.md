# Shared standalone header graph for SOLIDWORKS 2026

The archive layer in `src/convert/adapters/solidworks/Archive/Header/`
supports the standalone `Header2` and `Contents/Config-0-ModelHeader` streams
in the ordinary version-19000 profile measured on SOLIDWORKS 2026 SP05.2.
Each stream starts a fresh class and object map at 1, with one `moHeader_c`
root of schema 1. The reader consumes the complete stream. The writer
assigns references from object identity in traversal order.

| Owner | Field and framing rules |
| --- | --- |
| `moHeader_c` | Signed and unsigned 32-bit values keep distinct types. Native root objects use nullable typed archive tags. The bounds presence word follows the presence of the ten-double value, including the stored sphere radius. |
| `moExtObject_c` | Inline shared file definition comes first, followed by the provenance fields, inline selected configuration and three trailing values. The internal file name and display name retain their object identity through `moCStringHandle_c`. |
| `moExtObjectList_c`, `suObList`, `su_CStringArray` | The count follows the ordered typed tuple. Object lists write an archive tag for every position, including nulls. String arrays write characters in their selected source encoding. |
| `moLogs_c`, `moStamp_c` | Logs emit their stamp list before the identifier and name. Stamps keep three 16-bit fields, one 32-bit field and a name. |

The SDK reader preserves typed fields for each supported class alongside its
existing header and file projections. An absent self file is representable
in the graph. The drawing identity projection still requires a self file.
The profile rejects a nonnull configuration at `f28`, unknown classes
or versions a caller requests outside 19000. This codec covers the standalone
streams. The inline Definition header and other archive modes retain their
separate qualification paths. [Shared wire layouts](../../../src/convert/adapters/solidworks/Archive/Header/HeaderFields.py) · [Class read dispatch](../../../src/convert/adapters/solidworks/Archive/Header/HeaderClasses.py)

## Verification

Run `python re/tooling/sw2026/serial/CheckSdkHeaders.py FILE ... --report UNUSED.json`
with the disclosed input hashes in the receipt. The process extracts the
standalone header streams from those containers, constructs the typed
object graphs and requires exact re-emission. The audit records 31 streams
in 17 files spanning generated and native assemblies and their children,
and three blank drawing variants. It ran no native application phases,
tested no held-out input and created no CAD document. [Byte comparison receipt](../measurements/2026/SharedSdkHeaderGraph01.json)

The research metadata composition also passes its newly allocated graph
through the SDK codec. The conversion preserves identity of shared
strings, file references and revision log objects. Running the normal
guarded processes for two coincident inputs, one parallel input and one
driving distance input preserved the earlier complete parent and child
hashes. Each run reports zero input file reads during generation. The
synchronized assembly corpus process checks ten SDK header
reconstructions in its five disclosed input files.
[Generated graph bridge](../../tooling/sw2026/builders/HeaderGraphBridge.py) · [Synchronized assembly check](../../tooling/sw2026/serial/SyncedAssemblies.py) · [Coincident inputs](../measurements/2026/GeneratedCoincidentMateBundle01.json) · [Parallel input](../measurements/2026/GeneratedParallelMateBundle01.json) · [Distance input](../measurements/2026/GeneratedDistanceMateBundle01.json)

This work qualifies the shared codec for the measured stream shapes.
Complete semantic field classification, production writing and additional
release profiles remain open.

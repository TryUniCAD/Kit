# Shared SOLIDWORKS archive field definitions

The reader and writer now use the same wire definitions for these fields.
The refactor changes neither supported models nor accepted wire forms.

| Field | Reader before sharing | Writer before sharing | Shared definition |
| --- | --- | --- | --- |
| Standalone header bounding box | `ReadBoundsMut` | `StoreBoundsMut` | `HeaderBoundsField`: presence, scalar layout and bounds validation |
| Archive collection count | `ReadCount` | `EncodeCount`, `EncodeCountForm` | `CountField`: native and framework widths and extension markers |
| Object and class tags | `ReadTag` | `EncodeTag` | `TagField`: markers, reference width and class bits |
| CString frame | `ReadLength`, `ReadString` | `EncodeString` | `StringField`: length markers, unit widths and text encoding |
| Runtime class descriptor | `ReadTypeDescMut` | `WriteTypeMut`, `WriteHeadGraph` | `ClassDescField`: schema and name length widths and name encoding |
| Sized model section | `ReadSectionMut`, `ReadSectSpan` | `WriteSectionMut` | `SectionField`: skip mask and length prefix |
| Ghost manager word | `ReadGhostMut` | `WriteGhostMut` | `GhostWord`: signed flags and unsigned row count |
| Split row count | `ReadSplitMut` | `WriteSplitMut` | `SplitWords`: ordered halves and unsigned domain |
| Bounds and mass cache counts | `ReadCacheNumMut`, `ReadMassMut` | `WriteBoundsMut`, `WriteMassMut` | `CacheCountField`: count width, slot limit and mass selector presence |
| Fixed-size body bytes | `ReadBytesMut` | `WriteBytesMut` | `FixedByteField`: allowed width |
| Normalized body boolean | `ReadBooleanMut` | `WriteBooleanMut` | `BooleanField`: normalization of retained wire values |

Archive body layouts, manager schemas, and cache field order already use
shared field descriptors. Config root bounds use a different flag width
from standalone headers. Sketch projection and resolved-family serialization
remain separate. No populated ghost rows, bounds-cache rows, or alternative
view states were added. Canonical output and reader limits remain distinct
where the reader accepts noncanonical source representations.

The integration tests exercise standalone header and body graph writes,
plus mixed archive records in separate writer and reader processes. The
plain part candidate and its manifest were generated offline with matching
bytes before and after. These checks do not establish new vendor acceptance.

# CATIA V5 container

## Outer container

| Offset | Field | Encoding |
| --- | --- | --- |
| `0x00` | magic `V5_CFV2\0` | 8 bytes |
| `0x08` | directory offset | `u32be` |
| `0x0c` | directory length | `u32be` |
| `0x10` | fill `ff` | 8 bytes |
| `0x18` | fill `00` | 32 bytes |
| `0x38` | header flags | 8 bytes |

`directory_offset + directory_length == file_size`. The directory starts with
`CATIA_V5 CB0001\0` and ends with `CB__END`.

## Stream directory

Each descriptor has a logical length at `+0x0c`, an extent count at `+0x50`, and 20-byte extents
from `+0x54`. An extent is `physical_offset:u32be`, `physical_length:u32be`, `logical_length:u32be`,
`logical_offset:u32be`, and a trailing word. Outer extents are relative to file offset zero.
Nested extents are relative to the nested `V5_CFV2` magic.

The descriptor name is a UTF-16LE run before the descriptor. The standard form has a two-byte
terminator and one padding byte. The legacy form starts at `+0x10`.

## Nested container

The first nested `V5_CFV2\0` after outer byte 8 is the geometry container. Its directory offset is
relative to the nested magic. The standard part layout has one nested container with these streams:

| Stream | Role |
| --- | --- |
| `MAIN` | container root |
| `Describe` | document description |
| `MainDataStream` | topology spine |
| `Header` | stream header |
| `SceneGraph` | display graph |
| `SurfacicReps` | surface, curve, and vertex roster |

The largest `MainDataStream` and `SurfacicReps` descriptors are the B-rep streams. Repeated maximum
lengths leave the B-rep stream unselected.

## Outer declarations

The outer `Data` stream contains declaration records. A declaration has `01 00 03 00` at `+8`, an
ordinal at `+12`, `01 00 6c 00 02 00 00 00` at `+16`, and `02 00 81 20` at `+32`. Two NUL-terminated
ASCII class names follow at `+40`. The 16-byte identifier follows the names.

The 27-part corpus has eight declarations in this order:

| Ordinal | Class | Base |
| --- | --- | --- |
| 1 | `CATProdCont` | `CATFeatCont` |
| 2 | `CATPrtCont` | `CATProdCont` |
| 3 | `CGMGeom` | `CATFeatCont` |
| 4 | `CATMFBRP` | `CATFeatCont` |
| 5 | `CATSeeBodyCont` | `CATFeatCont` |
| 6 | `CATBRepModeContainer` | `CATFeatCont` |
| 7 | `CATStdCont` | `CATFeatCont` |
| 8 | `CATCGRCont` | `CATFeatCont` |

The `CGMGeom` stream contains the nested container. The nested physical base equals the first
`CGMGeom` extent physical offset.

## Evidence

- `src/convert/adapters/catia/Container.py` parses all 27 parts and 3 products.
- `re/catia/tooling/ListStreams.py` prints the stream inventory.
- `CATObjectModelerBase.dll` SHA-256 `a522a0a040c74fc8f53aea707785e0d00e836d9eb8a113a25349fbd985905980`.
- `CATStorageManager::InternalLoadAllContainers` at `0x18008f7f0`.
- `CATStorageManager::GetContainersToBeStreamed` at `0x18008de50`.
- `CATStorageManager::OmbDirectStreamCopyOfUnmodifiedStorage` at `0x1800902e0`.

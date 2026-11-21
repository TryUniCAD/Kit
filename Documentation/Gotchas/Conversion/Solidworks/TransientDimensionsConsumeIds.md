# Omitted dimensions can consume persistent ids

## Expectation

The header's next id follows only the objects emitted into the archive.

## Observed behavior

The 2026 from-end-spec constructor at `sldmodu` `0x4bad3e00` creates a role-19
parallel-plane-distance display dimension even when end type zero omits that
dimension from storage. Its parameter-naming path at `0x4c821c40` allocates the
dimension's `f50` unless the owner model reports viewer mode.

The fresh `moPart_c` virtual slot `0x1250` resolves through vtable
`0x4d1252d8` to `0x4c02d7d0`. With the naming caller's zero argument, it reads
model word `0x2b0` and returns the inverse of bit two. The model constructor
initializes that word to `0x0c`, so the ordinary fresh part is not a viewer and
the dimension consumes an id.

## Workaround

Construct the semantic transient dimension and allocate its actual `f50`
through the shared allocator, even when its conditional archive branch is absent.
Retain it in the construction state so repeated allocation and mutation checks
still apply. Derive the final header counter from that lifecycle; do not patch
in a fixed gap or derive the counter from serialized or visible feature count.

The [model construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
records the constructor and dispatch evidence. This rule establishes allocation
provenance, not target-application acceptance.

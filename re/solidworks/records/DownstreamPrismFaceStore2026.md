# Generated prism face validation and collector, SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns construction and native qualification. The modeled branch applies to an ordinary SOLIDWORKS 2026 SP05.2 `34.5.2.0604` part with one rectangular blind boss, six linked planar faces, and the ordinary direct face constructor. [Generated constructors](DownstreamPrismFaceConstructors2026.md)

## Key uses the ordered surface descriptions

The validator at `0x4b5254f0` first searches the original 32-bit key in its map at `+0x7a8`, then searches an alternate key made by swapping inline slots 1 and 2. It inserts only the current original key after both searches admit the row. A zero alternate key skips its lookup. The current face has already been appended to the face table when the validator runs, while its key is inserted into the key map afterward.

For the selected ordinary local part, the key text starts with ASCII `s,`. Append the nonnull representations in inline order. Each one contributes signed decimal words separated by commas. The next representation starts immediately at the preceding word's final byte. The null separator stays in the reference and contributes no key text.

| Representation | Key words in order |
| --- | --- |
| Extrusion cap | Kind 40, actual feature ID, signed creation-time word, effective local flags, cap selector, contour. A negative contour normalizes to -1. |
| Sketch-derived side | Kind 74, actual feature ID, signed creation-time word, effective local flags, sketch line marker. |

The local feature constructor's flag `0x10` is masked for key text. The part path uses no body prefix. The hash over the resulting ASCII bytes starts at zero with power one. Add each byte times the current power modulo `1000000009`, then multiply the power by `32771` with the same modulus. [Pinned key and insertion source](DownstreamFaceKeyOrder2026.md)

## Generated graph

The ordinary face witness checks its original and swapped keys against earlier original keys before retaining the constructor row. It refuses collisions. The two generated prisms have six distinct primary keys each and zero permanent edge attributes. Their six collector members follow the same linked primary face order. Each member is a new clone, with a separate file object starting at index `-1` and the original shared name and path handles. [Collector membership](DownstreamIdentityMembership2026.md) · [File copies](DownstreamCollectedSurfaceClones2026.md)

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckPrismFaceStore 1
```

Repeat with variant `2`. Two fresh processes per design reproduce the complete witness. An independent walk of the emitted partition calculates the six original and swapped key pairs from the actual kernel payloads and compares them to the typed reference graph. Varying the dimensions changes the container and cache bytes while preserving the feature and sketch identities and their hashes. Two synthetic collision inputs per design exercise rejection during original and alternate lookup.

The combined typed body retains six collector members and six face rows per design and round-trips with archive map counter 108. It preserves all eleven earlier generated part streams. Six additional processes reproduce their prior constructor, cylinder collector and cylinder clone receipts byte-for-byte. The guards recorded zero external operations after Python and field registry initialization. [Process receipt](../measurements/2026/DownstreamPrismFaceStore01.json)

That receipt records the earlier separately constructed surface graph. The current command reuses the actual collector objects in all face slots and reads back map counter 47. [Batch alias source and replay](DownstreamCollectedSurfaceOwnership2026.md)

Full cache population, native collision and replacement paths outside this scope, and native linked drawing load, rebuild, edit, save and reopen remain open.

# Generated prism cache lookup registration

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The registered graph covers fresh ordinary SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` rectangular boss part caches through edge-row registration. Root owns the typed projection and native qualification.

The generated partition's actual body, face and edge chains are verified against their attached allocation. The six retained face rows supply the associations of the twelve retained edge rows. Both lookup tables register the row ordinal, actual body atom and actual kernel node identifier. The two tables share the cache construction FILETIME. The ModelHeader update timestamp and kernel allocation timestamp supply independent fields. [Identity field source](DownstreamFaceRegistration2026.md) · [Retained edges](DownstreamPrismEdgeConstructors2026.md)

The ordinary prism allocates face IDs 1 through 6, then edge IDs 7 through 18. The fresh signed-key edge table grows from 8 buckets to 64 before linking the ninth entry. The rehash reaches empty destination buckets, and each final insertion appends at the shared sentinel. The stored entries follow the actual linked edge order. The generator admits this exact fresh profile and takes IDs and ordinals from the linked input and its already constructed rows. [Native edge lookup order](DownstreamEdgeRegistrationOrder2026.md)

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckPrismCacheRegistration 1
```

Repeat with variant `2`. Four guarded processes verify the actual partition's 24 registered edge identities and shared time across the retained graph. A one-tick edit changes only the emitted time words when the upper word does not roll over. Both caches preserve the prior eleven generated part streams, round-trip byte-exactly, and use map counter 104. An independent numeric replay verifies the lookup growth and order before comparing the rows read back from the container. [Process receipt](../measurements/2026/DownstreamPrismCacheRegistration01.json)

Late vertex population, final store conditions and native linked drawing qualification remain open.

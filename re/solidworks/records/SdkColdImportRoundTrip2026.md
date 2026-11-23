# Strict SDK round trips of cold local imported solids

Task `B04-SW2026-IMPORTED-BODY` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
The source inputs are the two pinned generated imports from the completed
2026 SP05.2 lifecycle. The [native receipt](../measurements/2026/GeneratedLocalBodyPartCompleted01.json)
binds the exact archives to SOLIDWORKS executable version `34.5.2.0604`,
two passing controls, cold read, rebuild, native save and fresh reopen.
The earlier rectangular and concave normal writer cases retain these digests.

| Imported solid | Bytes | Complete SHA-256 | Native candidate checks |
| --- | ---: | --- | ---: |
| Translated rectangle | 9,914 | `302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357` | 116 |
| Owned concave L prism | 10,890 | `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33` | 164 |

## Construction and source equivalence

The strict reader identifies the sole solid's resolved `moBaseBody_c` producer.
The construction input uses the actual oriented faces, carriers, trims and
neutral coordinates. The independent source projection comparison owns
geometry provenance, source identity and the derived neutral body link.
The ordinary generated part allocator builds the replacement native link.
Both planar compiler profiles, the completed-update model, the local Parasolid
encoder and the full archive composer are unchanged.

Before publication the normal import route hashes the complete regenerated
part and authenticates the native measurement. It strictly reads the new
bytes in memory and compares the entire neutral source projection, including
the imported producer, physical payloads, configuration and source identity.
The input's captured archive and kernel payloads serve only as comparison
witnesses. They supply no archive values. A canonical result returns all
preserved source capabilities as native transfers. The existing history
diagnostic still describes the imported solid.

## Evidence

The [guarded verifier](../../tooling/sw2026/imported_body_source/VerifyColdImportRoundTrip.py)
checks source projections from bytes and paths, neutral JSON and the registry,
direct writer and adapter. Separate macOS and Windows processes each record 12 exact public writes,
24 logical stream comparisons, 20 comparisons of mass properties against
native observations and 42 atomic refusals. The inputs include altered source
digests, source bytes, payloads, foreign properties and topology tolerances.
The guarded construction observes zero runtime file reads or CAD launches.
The alternate compressor path verifies unchanged logical geometry and
requires exact receipt refusal for different container bytes.

The evidence concerns exact republication of the measured generated shapes.
Intact vendor-saved imports, independent held-out cases, broader imported
geometry families and any original FCStd corpus credit remain open.
[Host receipt](../measurements/2026/SdkColdImportRoundTrip01.json) · [Windows receipt](../measurements/2026/SdkColdImportRoundTripWindows01.json)

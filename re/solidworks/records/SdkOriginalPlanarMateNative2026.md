# Original planar mate groups in the SOLIDWORKS 2026 SDK

Task `B04-SW2026-ASSEMBLIES-C10` in PR #121. Both pre-writer locked native
assembly inputs pass the full scoped internal SDK comparison. The scope is
resolved rigid direct occurrences of one generated dimensioned child with one
fixed anchor, one aligned coincident or parallel mate and one aligned positive
driving distance mate. The public assembly writer remains disabled.

## Source and executable custody

The [original author lock](../v2026/heldout/AssemblyPlanarMateSourceLock01.json)
identifies the original A20 and A21 parent/child pairs. The
[frozen method](SdkOriginalPlanarMethodFreeze2026.md) locks SDK code, source
admission, independent predictions and measurement tools in evaluation packet
`5f272f21111e28015729017c214c192635fea0d355fe54b8f0096957a7d944bc` before
either original was read. The root released each slot separately. Preparation
verified the immutable author recipe and original model hashes, translated
actual names and selected configurations through the strict reader, then
locked the neutral request and geometry prediction before construction.

Each slot ran two complete guarded builds with matching output and zero runtime
input file reads. The complete files also matched the independent mathematical
composer. The builder received authored model values and constructed the
native references, presentation and cache state. Neither original vendor
payload nor cache values were forwarded. The preparation receipts record
original source access separately from the guarded writer's file-read count.

## Native lifecycle

Each slot used the same five fresh phases in SOLIDWORKS 2026 SP05.2
`34.5.2.0604`. A22 controls bracketed the read-only original, a generated
open/rebuild/edit/save, and a fresh reopen of that generated save. The oracle
was driven through the Windows 11 VM by macOS `prlctl exec --current-user`
and COM `SldWorks.Application.34`.

| Original case | Direct occurrences | Ordered mates | Assembly / child tree rows | Initial → reopened distance | Numeric checks |
| --- | ---: | --- | ---: | ---: | ---: |
| A20 | 2 | Coincident, distance | 26 / 25 | 102.37 → 118.10 mm | 440 |
| A21 | 3 | Parallel, distance | 27 / 25 | 83.17 → 98.90 mm | 552 |

All ten applications were distinct. Every native open, rebuild and save gate
was clean. The original and generated parent and child match on ordered tree
rows, selected configurations, feature state, actual mate endpoint and child
ownership, solid count and geometry. Volume, area, centre of mass and the
reported mass agree at six significant figures for each separately measured
document. The assembly and child mass API values are retained independently.

Each live mate edit moved the predicted floating occurrence while retaining
the other mate, fixed anchor, rotations and all three child driving
dimensions. The child saved before the parent. Clean fresh reopen preserved
the actual child path and stamp, edited distance, geometry and native trees.
The original and frozen generated inputs remained hash-identical.

## Strict SDK readback

The original, generated and saved graphs retain their actual occurrences,
four ordered datum endpoints and three child driving lengths per slot. Both
saved parent/child pairs passed all 26 typed round trips across Config,
ResolvedFeatures, CMgr, CMgrHdr2, ModelHeader, Header2 and the parent
MatesList. The native-saved Definition, History, XML, geometry and other caches
are outside this stream audit. Each public read retains the legacy scanner's
informational `sldasm.native_record_unresolved` diagnostic.

The [sanitized measurement receipt](../measurements/2026/SdkOriginalPlanarMateNative01.json)
binds both raw native results, preparation and transport hashes, generated and
saved identities, and separate source and fresh-reopen geometry. This closes
the scoped original planar comparison. Broader assembly capabilities, all
public assembly output and original FCStd corpus conversions remain open.

# Native diagnostics for the generated ordinary prism cache

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The disclosed comparison uses SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` through `SldWorks.Application.34` in the reserved Windows 11 VM.

Each neutral rectangle generates two part files at known absolute guest paths. Both carry the same generated partition and its attached downstream attributes. The populated variant also carries `Contents/Config-0-DownstreamIdData`, with six collected surfaces and faces, twelve edges, and both lookup tables. No CAD input supplies any written data. [Typed cache projection](DownstreamPrismCacheRegistration2026.md)

## Native open and subsequent edit

| Profile | Original open error/warning | Live bodies before original rebuild | Original rebuilt volume, m³ | Edited depth, m | Fresh saved-copy open error/warning |
| --- | --- | ---: | ---: | ---: | --- |
| Prism 1, with and without populated cache | 0 / 32 | 0 | 0.000004693 | 0.009625 | 0 / 0 |
| Prism 2, with and without populated cache | 0 / 32 | 0 | 0.000005464875 | 0.012125 | 0 / 0 |

The warning is `swFileLoadWarning_NeedsRegen`. All four original parts rebuild to one solid without feature problems. Each pair agrees on volume, area and centre of mass, and the analytic check passes at six significant figures. The edited depth persists and the freshly reopened native copies start with one solid before rebuild. [SOLIDWORKS 2026 warning reference](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFileLoadWarning_e.html)

The exact-build packets record 16 distinct native processes, including four healthy bracketing controls. The save runs all report zero errors and warnings, emit separate artefacts, and preserve the original input digests. Each native saved copy omits the standalone downstream stream under the observed settings. The measurements leave real drawing cache consumption and original body restoration open. [Native receipt](../measurements/2026/DownstreamPrismCacheNative01.json)

Two more generated files omit downstream ID allocation and the cache stream. Their six local face tracking attributes each retain the timestamp with zero ID, type and owner key. Both still open with warning 32 and zero live bodies, then rebuild to the same one-body geometry. Two native controls pass around those measurements. The remaining first-open gate lies in the model and active partition path shared by the cohorts. [Unallocated partition receipt](../measurements/2026/DownstreamPrismUnallocatedNative01.json)

## Body clock and ordinary load route

Each of two shape pairs uses the same generated partition bytes and kernel body stamp of 102. A single later body event sets the model header counter to 103 in the comparison. Omitting that event leaves the header at 102 in the matching-clock input. Both variants of each shape still open with warning 32 and zero live bodies. The bracketed comparison therefore eliminates this one-tick mismatch as a sufficient explanation for the observed first-open failure.

A separate native save retains the original depth and geometry. It reopens with one body and zero diagnostics, with kernel and header body stamps of 107. The native active body uses a new atom, while the original generated atom remains in the saved atom table. These are observations of the native rebuild and save lifecycle. [Body clock and unchanged-shape receipt](../measurements/2026/DownstreamPrismBodyClockNative01.json)

The ordinary part loader selects its partition through `SolidStorage_c::LoadModel` and `moPart_c::loadExternalBodies`. It resolves model and feature marks in the actual returned partition. The compiled path identifies distinct checkpoints for receive, the body inventory, and publication into a model atom. This source boundary narrows the next runtime observation. [Ordinary partition load](OrdinaryPartPartitionLoad2026.md)

## Replay

Prepare each case with [the in-memory generator](../../tooling/sw2026/downstream/PreparePrismCacheNative.py). Give it variant 1 or 2, the actual absolute Windows part path, the document's integral model-time input, and an unused artefact output path. Select `--include-cache` for the populated case or `--omit-downstream-allocation` for the comparison with only local tracking. The generator rejects runtime file/process operations while it constructs the part and serializes its cache.

For the body clock comparison, pass `--later-body-updates 0` for the matching clock and `1` for the split clock. The added event advances the header body counter after the body and face assignments.

Run [the native measurement](../../tooling/sw2026/InspectPrismCacheEdit.py) through `prlctl exec --current-user` in the original VM with a job JSON and distinct receipt path. The job names the hashed bracketing control and each generated input and digest. Each case specifies the analytic initial and target depth, volume, area and centre, plus a separate native output path. The tool records the original open status before rebuild, then verifies the parameter edit and reads the edited file in a fresh process. The two disclosed variants are outside the held-out acceptance count.

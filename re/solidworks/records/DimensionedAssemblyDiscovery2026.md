# Dimensioned assembly discovery on SOLIDWORKS 2026

The [inspection runner](../../tooling/sw2026/InspectDimensionedAssembly.py) measures two disclosed synchronized assemblies. A13 contains one identity occurrence. A14 contains identity and a second occurrence rotated −71.317° around Y with translation `(0.08973, −0.04413, 0.01731)` m. Each pair has one ordinary external child, `CohortChild.SLDPRT`, and one `Default` configuration. The [source tree receipt](../measurements/2026/AssemblySyncTreeTopology03.json) binds the source locks and records 23 and 24 recursive assembly nodes, including Markups, Notes under Annotations, and occurrences before Mates.

The generated pairs use independently authored rectangle ladder intent, geometry and dimension text anchors. Their baseline is a centered 0.04 × 0.02 m sketch with a 0.01 m blind depth, `Sketch1` and `Boss-Extrude1`. The generated child requests English standard names, an Annotations cabinet and the distinct `moInkMarkupFolder_c` Markups role. The generated assembly uses the standard folder names and assembly root layout described in the [presentation ledger](AssemblyPresentation2026.md). The output path is part of each writer request. It names that trial's generated side so a native open can check direct binding. [Rectangle fields](RectangleDimensions2026.md), [neutral presentation request](../../../tests/Convert/Solidworks/Research/Presentation/MakeTreeInput.py), and [assembly root request](../../../tests/Convert/Solidworks/Research/Assembly/RootRequest.py).

## Frozen discovery inputs

| Item | SHA-256 |
|---|---|
| `Job.json` | `020d916d66cd9c828326386a77dd8721a949978873b2f83ce59d8cb50b721757` |
| `SourceSnapshot.json` | `0b98424bea193258b1cb135170113bc7b3f7eb3df0bc4ee11a4ebad0cfd72e6b` |
| `WriterSources.json` | `0a0e6a32aa795029e5d426d77e9f8e530184003716683f96d653bf798bfd4027` |
| `OracleTools.json` | `91cf553844446c03645c403a11e213f627449853f446c4c22543a10602f31ece` |
| `InspectDimensionedAssembly.py` | `12bed9711b87030526699684a9131fae3689c1cd43302c10f8fdce2b41583af1` |
| Native executable, build `34.5.2.0604` | `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe` |

Writer revision `23e01579fb0ad607417ddfc84e4fbb7b0c55b1be` and tree `1d6a9ee722f57e061725b43671498bf6fa3968e2` bind the [research bundle process](../../tooling/sw2026/AssemblyRootProcess.py). The helper sources in `OracleTools.json` use that same revision under `re/tooling/sw2026/`. `Job.json` binds all six generated pairs and their neutral request and structural check receipts. Writer-process guards, independent archive reads and hash verification passed in local preflight. The child readback confirms both rectangle dimensions, their sketch ownership and one top-level Markups role. The parent readback checks occurrence and configuration ownership, directory references and registry reserialization.

## Native observation

Stage the `DimensionedAssemblyDiscovery-3c82` deck in the Windows oracle's `C:\Users\Public\Documents\KitOracle` directory and run `python OracleTools\InspectDimensionedAssembly.py Job.json` from the deck. The job reserves `Inspection/` for its results. Run the job through the same process-ownership and licence-preserving transport used for previous batches.

Each trial edits one driving dimension by its native parameter name. The width target is 0.05 m, height 0.025 m and depth 0.0125 m. Each edit starts from separate exact copies of the source and generated pair. The source edit phase preloads its own relocated child. The generated phase verifies its encoded reference by opening the parent directly. Every occurrence must resolve to the staged child. Save the edited child explicitly, save the assembly beside it, then open that edited assembly directly in another process and compare the child state and build stamp. The staged source and generated artifacts are hashed again after the run. [Synchronized save scope](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/AssemblySaveCanLeaveChildStampUnsaved.md).

The runner records exact recursive native feature trees, occurrence counts and names, rigid placements, configuration names, driving values, solid body counts, volume, surface area, centre of mass and mass for every measured scene. Width and height edits can translate the unconstrained profile in its plane. The analytical centroid checks the depth coordinate, while native comparisons check all three coordinates. The native assembly mass and isolated part mass APIs have different effective defaults, so assembly mass is compared to the corresponding source assembly. [Mass scope](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/AssemblyMassCanDifferFromPartMass.md).

`Inspection/Inspection.json` records both document controls, the tool hashes, independent process births and comparisons before edit, after edit and after synchronized save and fresh reopen. Individual `EditRun.json` and `SavedReopen.json` receipts retain stage and COM error details.

The [native measurement](../measurements/2026/GeneratedDimensionedAssembliesNative04.json)
passed six independent single-dimension trials across 26 fresh processes. Each generated
trial matched the corresponding measured native assembly and child before its edit, after
the edit, at synchronized save and on fresh reopen. The single- and repeated-occurrence
parents preserved 23 and 24 recursive nodes respectively. All child trees preserved 25
nodes. The geometry, transforms and all three driving values matched. The staged sources
remained immutable. Both controls passed and A15/A16 remain sealed.

# Explicit part-material source protocol on SOLIDWORKS 2026

Task `B04-SW2026-NAMED-MATERIAL`, PR #121. Root owns all Windows execution and source custody. This source-authoring method generates native **oracle inputs**, not Kit writer output. No material writer or public registration is added. No original hidden payload or saved material row is read by the preparer.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), full [instruction book](../../Playbook/README.md), [GenerativeCorpus](../../Playbook/GenerativeCorpus.md) and [WriterModel](../../Playbook/WriterModel.md) apply. The earlier [owner map](AssignedMaterialOwners2026.md) supplies exact static boundaries; it does not qualify assigned-material generation.

## Catalog and API custody

Root's exact model-free query result has SHA-256 `9598ba4c5e9d103f4af11b802bc12c49a0160495e2fd3f184376e7d9b81d74b7`. It used one fresh pinned process, zero model documents, zero preference changes and a confirmed idle graceful exit; the independent transport records unchanged FlexNet and zero remaining SOLIDWORKS PIDs. The registered 34.0 generated Python wrapper has SHA-256 `d8982a8caef31e4c62ed49b70d3747f701fee0622bbaec7a550d6e874327e959`. The static Python signature observation has SHA-256 `04c5eb971a5fb7b1616b7d9f7ecab195fe037431999533b6cacae2cd761e7ce4` and launched no CAD process.

Both part and body material getters have a BSTR return plus an output database BSTR. Their generated Python signatures default the database argument to `PyOleMissing`; they have no return annotation. The new observer logs the actual native Python return type, element types and values **before** requiring the two-output representation. Null BSTR and empty BSTR are both normalized to the documented blank identity while their raw distinction remains recorded. It does not infer a successful database identity from a material-only string. An unexpected shape stops the source trial with its observations retained.

Two actual installed catalog entries define a discriminating hypothesis:

| Key | Database | Material | Captured `DENS@value` | Database SHA-256 |
| --- | --- | --- | --- | --- |
| A | `solidworks din materials.sldmat` | `3.0205 (EN-AW 1200)` | `2700` | `1290afbb47e04e9900337722f8aa09eccdf5152288e66c101129f0a47aa0fff8` |
| B | `solidworks materials.sldmat` | `1023 Carbon Steel Sheet (SS)` | `7858.000032` | `636ef75ffb10e8abf7529c910a50dc2cb0d73ce5112c9721e7e4de1824cf57c5` |

The XML value is an **attribute**, not a child node. The earlier capture's `raw_value` is empty, but its attribute metadata retains the actual observation. The installed XSD is hashed as `2afeff3c0983fc895ec724a20a84a96991f795f032e2d6ba73179ddfbaac7657`; Python ElementTree rejected its bytes at line75/column2. This is an observer result, not proof that the native schema or database is invalid. No SI density claim is based on that schema parse. See the [metadata gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Materials/MaterialDensityCatalogValuesNeedNativeUnitChecks.md).

The source job explicitly predeclares the hypothesis `density_SI = 1 * DENS@value`. Packet 03 measures native density, mass and volume in SI on the selected solid. Each assigned state must satisfy native density, native mass divided by independent analytic volume, native mass divided by native volume, and predicted mass `rho * width * height * depth`. A disagreement fails the source trial and retains the measurements. The density prediction stays fixed.

## Disclosed designs and lifecycle

D01Corner is a fully anchored Front rectangle, 17.125 × 23.75 × 8.625 mm, edited boss depth11.375 mm. It starts with A and changes to B. D02Center is a fully anchored Front rectangle, 28.375 × 13.625 × 11.75 mm, edited boss depth7.625 mm. It starts with B and changes to A. They use the existing native `RectangleAuthor`, actual three driving dimensions, actual model origin and independent prism math. All configuration names are explicit `Default`.

Each design runs in four fresh processes:

1. Author the actual anchored rectangle/boss, measure its unassigned state, author a pure RGB/reflectivity appearance contrast, verify unchanged assignment identity/mass, assign the first actual database material, verify analytic shape and physical mass, save `Original.SLDPRT`
2. Fresh-open immutable Original with zero diagnostics, verify the first assignment, change to the second material with fixed geometry, require mass ratio `rho_second/rho_first`, save separate `Swapped.SLDPRT`
3. Fresh-open immutable Swapped, verify the second assignment, edit actual `D1@AnchorBoss`, require correct new geometry, density and mass ratio `depth_new/depth_old`, save separate `DepthEdit.SLDPRT`
4. Fresh-open immutable DepthEdit read-only and repeat the complete geometry, three-driver, origin/constraint, assignment and physical-mass checks

The same pristine existing rectangle control with SHA-256 `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57` brackets the two designs. All ten processes must be distinct with healthy controls. Open/rebuild/save errors and warnings must all be zero. Every input is rehashed after its phase, and both installed material databases are rehashed before and after the batch. No database, system preference or license process is modified.

The complete recursive feature trees and actual part/body material API fields are retained. Material-only comparisons preserve real profile geometry, driving dimensions, origin relations and tree structure. Only the native `MaterialFolder` caption has an explicit presentation comparison rule; its actual name is still recorded. No arbitrary row is dropped to force a count. Part assignment and inherited/body-specific material getters are recorded separately. This does not qualify body overrides, multibody precedence, mass overrides, missing databases or a material writer.

## Frozen packet 02 and invocation

The retained `NativeSourcePacket02.json` manifest has SHA-256 `342283c9e952693fba073c5171a904861dbbcd25e46ed3e10d5d5fc3147fd2c1` and binds 13 files. Its Job SHA-256 is `292df06a2fd4f740c2070a32152568271eaf1c95be2675a9564e541f4c0b677f`. Packet 02 adds Intent-file verification and uses the legacy part mass getter for its comparisons. Packet 01 is retained.

Exact tool copies in the historical packet:

- `AuthorAssignedMaterials.py` has SHA-256 `daac77bea3a87c010924229912f1a5c05b5ccf2426ff38f35cf9b89003b13cd9`
- `MaterialSourceFacts.py` has SHA-256 `565084d5ab51db40366d42bd8bbbf1b5cd73afd24afd20a56e5905c303275a81`

Their exact dependencies are copied into the private packet's `Tools` directory. Root must commit the exact oracle sources before the run, independently hash all packet members and invoke the host-verifiable `verify` action. The new tools emit no native CAD bytes themselves; SOLIDWORKS authors the source controls.

The historical guest invocation used the verified Python 3.12 executable.

```powershell
py.exe -3.12 '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\SdkNamedMaterial01\NativeSourcePacket02\Tools\AuthorAssignedMaterials.py' run '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\SdkNamedMaterial01\NativeSourcePacket02\Job.json' --packet-sha256 292df06a2fd4f740c2070a32152568271eaf1c95be2675a9564e541f4c0b677f
```

The host command is the same argument list prefixed with `prlctl exec --current-user "Windows 11"`. Replace `py.exe -3.12` with root's known verified executable path if the launcher is absent. No native run was executed by the preparer.

Progress/terminal output is `NativeSourcePacket02/Inspection/Result.json`; each phase retains its own `Record.json`; Original-file hashes and intent/observer joins are written to `Inspection/SourceLock.json`. SourceLock creation alone is not qualification: both native brackets, all ten phases, persistence and the predeclared density hypothesis must pass.

## First-writer lock protocol

1. Preserve the immutable disclosed packet, actual catalog/schema/API metadata and its terminal result, including any failure
2. Before material writer code, root uses the same frozen author/observer semantics in a **separate root-private sealed-original cohort**, choosing two independently dimensioned and hidden source intents; the preparer and writer agent do not receive its cases or observations
3. Root records source Original hashes, intent hashes, exact source-author tool closure, catalog/schema hashes, native build, native source edit/save/reopen sidecars and successful control outcomes in a metadata-only registered lock; filenames/hashes may be exposed, hidden values and payloads remain sealed
4. Mapping and generative constructor work use only the disclosed source cohort and exact native rules; no material database row, captured stream, field program or XML payload becomes a writer seed
5. Freeze the writer source, semantic source-to-neutral mapper, independent predictor, exact input/output manifest and complete comparison criteria before root permits any original hidden access
6. Root alone attaches the sealed original intents under that method, runs source/generated native lifecycles between healthy controls and counts only complete compared source semantics; failure or an unrepresented owner remains an explicit refusal

No hidden qualification is claimed by this disclosed source packet. The original source lock is not retroactively supplied by new post-writer authoring. Public material registration remains gated.

## First native result

Packet 02 failed both physical-density assertions through the legacy part getter. Four distinct SOLIDWORKS 2026 SP05.2 processes include two healthy bracketing controls. The actual part getters return each requested material and catalog after an ordinary forced rebuild. The explicit body getter remains empty. The legacy density and mass-to-volume ratio remain 1 kg/m³ in the assigned, unassigned and visual-only states. Both author phases stop before saving and lock zero originals. [Compact failed result and exact phase digests](../measurements/2026/AssignedMaterialDensitySource01.json)

The follow-up diagnostic authors the same corner geometry with the same catalog assignment and omits the visual-only perturbation. All four phases pass with two healthy controls. The selected-body `IMassProperty2` gives 1000 kg/m³ unassigned and 2700 kg/m³ assigned and after save, fresh read-only reopen and rebuild. Volume matches the legacy path throughout. The legacy path still gives 1 kg/m³, so the historical combined-API density predicate remains false. The diagnostic saved file is bound by hash in the receipt. [Original diagnostic observer](../../tooling/sw2026/materials/ObserveMaterialDensity.py) · [Selected-body diagnostic receipt](../measurements/2026/AssignedMaterialDensityProbe01.json)

## Packet 03 selected-body measurement

The actual sole visible solid must be a `Body2` with solid type. The observer clears selection, selects that body, obtains `IModelDocExtension.CreateMassProperty2`, sets `UseSystemUnits`, recalculates and records volume, mass and density. It clears selection in a finally block. The legacy observer still records volume, area, centre of mass, mass, density and override flags. Geometric predictions are checked against both volume paths. Physical mass, density, mass-to-volume and edit-ratio assertions use the selected-body observations. The visual-only contrast, requested dimensions, actual parameter identities and original `DENS@value` predictions stay the same. [Current native author](../../tooling/sw2026/materials/AuthorAssignedMaterials.py) · [Current measurement helper](../../tooling/sw2026/materials/MaterialSourceFacts.py)

Freeze the two disclosed cases from a committed checkout.

```sh
python -I -B re/tooling/sw2026/materials/FreezeMaterialSource03.py freeze /path/to/NativeSourcePacket02.json --revision "$(git rev-parse HEAD)"
```

The freezer checks all 13 old members by digest and copies only the declared input inventory into a newly created sibling `NativeSourcePacket03`. It replaces the author and facts tools from committed Git objects, writes the corrected observer declaration and updated tool hashes to Job, and invokes the new packet's non-native `verify` action. Neither the prior packet nor its result is opened for writing. The returned Job SHA-256 is the value for the root guest command's `--packet-sha256` when substituting `NativeSourcePacket03` in the historical arguments above. The final sibling manifest carries all input digests.

## Disclosed lifecycle result

Packet 03 completed all four source phases for both designs and both controls. The selected-body observer measures `2700` and `7858.000032` kg/m³ in the expected initial and swapped states. Both depth edits, saves and fresh read-only reopens passed. Ten distinct SOLIDWORKS 2026 SP05.2 processes executed 904 numeric candidate checks. The terminal result SHA-256 is `cb044d2a615d819e8ac642f3eea4bf5f313b8b61c5bd70570e7e3c90895a26f1`. Its two disclosed originals are bound by SourceLock SHA-256 `c3df77f9b43fb272d16c92da59dc22486e6dd6c8c503c322dcd23fe20960ecba`. [Native result](../measurements/2026/AssignedMaterialSourceNative01.json) · [Binary density and material tree comparison](AssignedMaterialArchiveOwners2026.md)

## Root-owned pre-writer material source lock

The [sealed source launcher](../../tooling/sw2026/materials/SealAssignedMaterialSources.py) checks the exact packet 03 manifest and all 13 member hashes before trusting its terminal result and source lock. Check that the pinned launcher revision retains the pre-writer source tree `2d2f36df71ef1a9261369ee8fbbc07143a2bb138` and freeze the source lock before introducing material writer code. Wait for the disclosed trailing control and teardown before starting the private batch.

The guest reserves a new folder directly on its fixed C drive. It copies the seven disclosed source tools, the control, and the two metadata files byte for byte. It samples both new designs inside the guest with system cryptographic randomness. Their neutral width, height, original depth and edited depth use bounded positive micrometre values distinct from the disclosed dimensions. The corner grows and the centered part shrinks, preserving the original fully constrained rectangle profiles and the opposing A/B assignments. The material catalog references and SI predictors remain exact. A private commitment binds the authored intent hashes, the unchanged tools and the new Job before launch.

The same source author verifies and runs the local Job under `sealed_original`. The ten ordered phases require the pinned executable, distinct process identities, healthy controls, zero save/open diagnostics and the same 147, 118, 114 and 73 numeric checks per design. The launcher rehashes each phase record, source and derivative and verifies the original intent/file/record join. The raw result, private intent files, detailed observations, native CAD and logs remain in the local private folder. The exported receipt contains opaque slots, masked intent commitment, file and phase digests, check counts and aggregate verdicts.

Run the non-native host preflight with the exact disclosed manifest.

```sh
python -I -B re/tooling/sw2026/materials/SealAssignedMaterialSources.py preflight /path/to/NativeSourcePacket03.json
```

It verified the 13 members and all 10 disclosed phases, exercised the receipt filter with synthetic opaque aliases, and refused one missing numeric check. Native process and private input counts were zero.

Root runs the frozen launcher with the verified current-user guest Python 3.12 after the host preflight. The receipt destination is a new file outside the private C folder.

```powershell
py.exe -3.12 -I -B <launcher> seal <NativeSourcePacket03.json> --revision <committed-launcher-revision> --tool-sha256 <launcher-sha256> --private-root 'C:\KitSealedMaterialSource02' --receipt <new-public-receipt>
```

### Current-user interpreter calibration

Lease 01 reached private Job verification. Its native child then raised `ModuleNotFoundError` during `Swapp` import under `-I -B`. Isolated mode hid the current-user pywin32 installation. No `Inspection` directory or native process was created, and the attempt produced no original source lock. Its private intent commitment and log stay with the failed lease.

The child now uses the same pinned executable with `-E -B`, matching the successful disclosed batch. This ignores Python environment variables, keeps bytecode disabled and preserves the installed user-site COM imports. Lease 02 requires a fresh C folder and receipt path. Source, phase and custody checks still use the exact packet 03 rules. [Related observer import gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Rewrite/IsolatedPythonHidesUserSiteComObservers.md)

Keep private values and source files sealed through writer and comparator freeze. This prospective source lock will supply original controls for the material writer evaluation. Held-out comparison and public writer acceptance require later evidence.

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

The source job explicitly predeclares the hypothesis `density_SI = 1 * DENS@value`. Every assigned state must independently satisfy native `IMassProperty.Density` with `UseSystemUnits=True`, native mass divided by independent analytic volume, native mass divided by native volume, and predicted mass `rho * width * height * depth`. A disagreement fails the hypothesis and source trial; no observed density is substituted into a passing predictor after the run.

## Disclosed designs and lifecycle

D01Corner is a fully anchored Front rectangle, 17.125 × 23.75 × 8.625 mm, edited boss depth11.375 mm. It starts with A and changes to B. D02Center is a fully anchored Front rectangle, 28.375 × 13.625 × 11.75 mm, edited boss depth7.625 mm. It starts with B and changes to A. They use the existing native `RectangleAuthor`, actual three driving dimensions, actual model origin and independent prism math. All configuration names are explicit `Default`.

Each design runs in four fresh processes:

1. Author the actual anchored rectangle/boss, measure its unassigned state, author a pure RGB/reflectivity appearance contrast, verify unchanged assignment identity/mass, assign the first actual database material, verify analytic shape and physical mass, save `Original.SLDPRT`
2. Fresh-open immutable Original with zero diagnostics, verify the first assignment, change to the second material with fixed geometry, require mass ratio `rho_second/rho_first`, save separate `Swapped.SLDPRT`
3. Fresh-open immutable Swapped, verify the second assignment, edit actual `D1@AnchorBoss`, require correct new geometry, density and mass ratio `depth_new/depth_old`, save separate `DepthEdit.SLDPRT`
4. Fresh-open immutable DepthEdit read-only and repeat the complete geometry, three-driver, origin/constraint, assignment and physical-mass checks

The same pristine existing rectangle control with SHA-256 `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57` brackets the two designs. All ten processes must be distinct with healthy controls. Open/rebuild/save errors and warnings must all be zero. Every input is rehashed after its phase, and both installed material databases are rehashed before and after the batch. No database, system preference or license process is modified.

The complete recursive feature trees and actual part/body material API fields are retained. Material-only comparisons preserve real profile geometry, driving dimensions, origin relations and tree structure. Only the native `MaterialFolder` caption has an explicit presentation comparison rule; its actual name is still recorded. No arbitrary row is dropped to force a count. Part assignment and inherited/body-specific material getters are recorded separately. This does not qualify body overrides, multibody precedence, mass overrides, missing databases or a material writer.

## Frozen packet and invocation

The private `NativeSourcePacket02.json` manifest has SHA-256 `342283c9e952693fba073c5171a904861dbbcd25e46ed3e10d5d5fc3147fd2c1` and binds exactly13 files. Its Job SHA-256 is `292df06a2fd4f740c2070a32152568271eaf1c95be2675a9564e541f4c0b677f`. The unused packet01 is retained; packet02 adds redundant Intent-file verification without altering case intent or the catalog hypotheses.

New source tools:

- [AuthorAssignedMaterials.py](../../tooling/sw2026/materials/AuthorAssignedMaterials.py), SHA-256 `daac77bea3a87c010924229912f1a5c05b5ccf2426ff38f35cf9b89003b13cd9`
- [MaterialSourceFacts.py](../../tooling/sw2026/materials/MaterialSourceFacts.py), SHA-256 `565084d5ab51db40366d42bd8bbbf1b5cd73afd24afd20a56e5905c303275a81`

Their exact dependencies are copied into the private packet's `Tools` directory. Root must commit the exact oracle sources before the run, independently hash all packet members and invoke the host-verifiable `verify` action. The new tools emit no native CAD bytes themselves; SOLIDWORKS authors the source controls.

Root guest invocation using its already verified Python312 executable:

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

The physical-density hypothesis failed on both disclosed source designs. Four distinct SOLIDWORKS 2026 SP05.2 processes include two healthy bracketing controls. The actual part getters return each requested material and catalog after an ordinary forced rebuild. The explicit body getter remains empty. Both legacy native density values and independently calculated mass-to-volume ratios remain 1 kg/m³. The unassigned and visual-only comparison states also measure 1 kg/m³. Both author phases stop before saving. Zero original sources were locked. [Compact failed result and exact phase digests](../measurements/2026/AssignedMaterialDensitySource01.json)

The [follow-up diagnostic](../../tooling/sw2026/materials/ObserveMaterialDensity.py) authors the same corner geometry with the same catalog assignment. Its transition omits the visual-only perturbation. It measures the actual sole body with the newer selected-body interface and the original part interface, saves a separate diagnostic file, and measures it again in a fresh read-only process. The same known controls bracket the run. Assignment identity, file persistence and physical density have independent verdicts. [Mass-property API relationship](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IMassProperty.html) · [Selected-body measurement interface](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IMassProperty2_members.html?id=2.2.1.211.0)

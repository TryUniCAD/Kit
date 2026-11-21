# Independent assembly identities and the planar VisualStates boundary

Task `B04-SW2026-MATES-PLANAR/source-identity`, owner `assembly_frontier`, delivery PR #121. Both prior A20 and A21 originals still refuse whole-source writing. The shared constructor now transfers their independent model and file identities, and the strict SDK reader joins the measured third all-visible occurrence. The linked VisualStates lane remains closed. [Prior root projection](SdkPlanarRootSourceProjection2026.md) · [Guarded receipt](../measurements/2026/SdkPlanarAssemblyIdentity01.json)

## Confirmed identity owners

The exact source pairs are from the earlier disclosed cohort. No new held-out input supplied any construction rule. The inventory binds the ordinary version-19000 Config-0 graph, both headers, the selected CMgr configuration and the two separate XML streams. [Custody](../v2026/heldout/AssemblyPlanarMateSourceLock01.json)

| Owner | Actual A20 and A21 value or rule |
| --- | --- |
| `Config-0.moAssembly_c.f18` model name | `Assem1` |
| Both header self `moExtObject_c.shared.h10` handles | `Assem1` |
| Both header self `shared.h18` handles | Empty Unicode text in the native originals |
| Selected CMgr configuration and header `refcfg` | Persistent ID 0, name `Default` |
| Instance-tree `swConfiguration.swReference` | Actual binary model name `Assem1` |
| Instance-tree assembly `swFile.swPath` | Actual external file locator |
| Both instance-tree `swModel.swName` captions | Actual assembly file stem |
| Root `KeyWords.Name` | Actual binary model name `Assem1` |

`AssemblyInput.NameValue` continues to validate the external stem against the explicit `SelfFileInput`. An optional checked `ModelName` supplies the root's independent native name. The existing archive rules propagate that root name to both header name handles, the keyword tree and the active configuration reference. The target's explicit new locator populates both generated header path handles and the instance tree. The originals' empty header path representation remains in custody. The constructor uses the explicit destination path it already requires. [Constructor input](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/AssemblyInput.py) · [Validation](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/CheckAsmMeta.py) · [Graph composition](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/MakeAsmBase.py)

## Confirmed XML ownership

The normal strict A20 read is byte-identical to the original SDK wire. A21 adds only `assembly.attributes.typed_display_states` and its derived source semantic seal. It binds `Default` configuration 0 to one all-visible state named `Display State-1`, with XML list/state IDs 9/10 and ordered actual persistent references 24, 25 and 26. The one- and two-member paths keep the previous guards, and mixed visibility, foreign model aliases and inconsistent occurrence order refuse.

An isolated in-memory writer observation joins the semantically named state against the actual generated occurrence graph. Counts and XML list/leaf IDs are allocated from that graph. A20 yields list/state IDs 8/9 and references 24 and 25. A21 yields list/state IDs 9/10 and references 24 through 26. The XML is measured independently of the generated parent bundle. The ordinary parent archive cannot publish the requested whole display until the accompanying binary owners qualify. [XML reader](../../../src/convert/adapters/solidworks/Assembly/Display/ReadDisplayXml.py) · [Binary configuration join](../../../src/convert/adapters/solidworks/Assembly/Display/CheckDisplay.py) · [In-memory XML composition](../../tooling/sw2026/para/concentric/MakeDisplayTree.py)

## Guarded same-input comparison

The verifier extracts the exact pre-change SDK at `b18caa86c15d2c65ad95c9a572bbc9d06701da8c` as Python source and runs its normal strict read in a separate process for each pair. All 12 successful guarded reader and builder processes are distinct, with four additional guarded writer refusal workers. Constructor requests contain semantic input only and log zero runtime input reads. The original strict neutral wires, including source diagnostics and native appearance evidence, remain in private reversible custody.

The no-alias bundles match the pre-change bytes at the same input, event and locator. The independent alias path changes just CMgr, Config-0, Config-0-ModelHeader, Header2, COMPINSTANCETREE and KeyWords. The other stream identities, actual occurrence placements and ordered constraints remain equal. The label-aware generated child is unchanged, including both original XYZ text points and centreline routing. Both alias paths repeat deterministically. The verifier retains no generated CAD file.

## First actual appearance refusal

Passing the requested display through the actual `EmitAsmStreams` entrance fails in `CheckAsmDisplay` with `assembly visibility requires the ordinary radial child without a visual store`. The generated linked part is the actual rectangle `BlindPlan`. The check occurs before any appearance emission. The existing radial profile also requires an aligned unlocked concentric mate, two references and a three-state visibility vector. None of those guards were relaxed. [Writer entrance](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/EmitAsmStreams.py) · [First guard](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Displays/CheckAsmDisplay.py)

The two source parent stores replay all 1,247 and 1,439 bytes with terminal maps 38 and 44, zero opaque or provisional operations and no tail. Actual component context rows join their live configuration in reverse occurrence order. They carry context word 203 and bind live persistent IDs 25/24 for A20 and 26/25/24 for A21. The separate three plane rows retain the measured creation owners. Both child stores independently replay the same 1,789 bytes at terminal map 26. They contain six entity rows and one populated part-self appearance, joined through the holder row's sibling `visStateVisualPropertiesAttribute_c.f10 → moVisualProperties_c.f20.f90` with material ID words `[3, 0]`. Source replay proves wire owners and does not authorize the appearance preset, native cache precedence or an omission rule. [Parent store construction evidence](ConcentricVisualStateStore2026.md) · [Child appearance owners](ConcentricChildAppearance2026.md)

A source-aware follow-up needs the independent planar parent default-store construction, the actual rectangular child appearance allocator/preset semantics, and controlled native persistence. The raw originals continue to fail the earlier root guard with `assembly root contains unprojected model content`. The current artifacts earn zero whole-source writing and native acceptance credit.

```sh
PLANAR_IDENTITY_PROOF="$(mktemp -d)/Proof"
python3.14 -I -B re/tooling/sw2026/planar_registry/ProvePlanarAssemblyIdentity.py prove \
  --disclosed /absolute/path/to/Oracle121Takeover \
  --output "$PLANAR_IDENTITY_PROOF"
```

Only the sanitized `Receipt.json` enters Kit. The private output separately retains the complete original document and inverse custody. [Verification tool](../../tooling/sw2026/planar_registry/ProvePlanarAssemblyIdentity.py)

The later internal planar composition supports both parent display owners and a separately modeled constructor-only rectangular child appearance. The original populated renderer, allocator and feature clock evidence remain independent whole-source stops. [Guarded composition and current boundary](SdkPlanarVisualComposition2026.md)

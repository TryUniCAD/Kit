# Measured ordinary revolve end-mode publication

This slice extends [the principal revolve delivery](https://github.com/TryUniCAD/Kit/pull/244)
with the existing model-only construction for four disclosed Top-plane
profiles. The part writer creates the end object and its actual
angle display owners through the common archive graph. The original
serializer and native evidence are documented in
[ordinary end-mode fields](https://github.com/TryUniCAD/Kit/blob/0e8673133c0c82152a80acab9b502b1a3990e329/re/solidworks/records/OrdinaryRevolveEndModes2026.md).

The Mid Plane wire uses one positive total angle. The Two Directions
wire owns two display, dimension and parameter chains. Reverse affects
the selected axis sense while D1 and D2 retain their roles. The strict
reader checks the allocated angle nodes against those actual chains and
derives the closed result from the signed interval, actual line and
profile incidence. Both sketch endpoint types use the same
metre-to-millimetre division, preserving an exact inverse for the
measured finite axis endpoints.

| Case | Measured archive bytes | Exact SHA-256 | Drivers |
| --- | ---: | --- | --- |
| EndSingle | 8079 | `8147cdc67c6fd3a760cc3c80e8fca490d97f709f5468abfc32abcaf6f5dee862` | D1 |
| EndMidplane | 8091 | `d4a942574936ee1ac580aae5f6f33c3e2213be89fce211231b913b5521b8adb4` | D1 |
| EndTwo | 8196 | `6d8d020e57daf676b9f0315475d92e268ac177dfaa4e74c31df2de53a4c78b77` | D1, D2 |
| EndTwoReverse | 8217 | `65f21b513348454d05a88a3c473a43062146b110e2161bc2db13900f50f8e7ab` | D1, D2 |

The [generated-file witness](../v2026/corpus/revolve/MeasuredEnd01/Generation.json)
records only the linked owner observations and stream identities. The
[job](../v2026/corpus/revolve/MeasuredEnd01/Job.json) binds the actual
measured self locators. The
[native result](../v2026/corpus/revolve/MeasuredEnd01/Result.json)
preserves the previously observed SOLIDWORKS 2026 SP05.2
`34.5.2.0604` process batch. Eight candidate phases launched in fresh
processes with two healthy bracket controls. Fourteen matched
geometry and edited states retained 19 ordered top-level tree rows and
passed 84 numeric comparisons. The original native result uses CRLF.
The exact Git LF text authenticates against the same original
observation digest. All original candidate and log hashes are kept
in the evidence.

## Process verification

Run the same command in a fresh process for each case.

```sh
python3.14 -I -B re/tooling/sw2026/revolve/ProveMeasuredRevolveEnds.py --case EndMidplane
```

The independent proof can also take `--disclosed` with the original
`RevolveEndGenerated01` directory to compare the generated binary
against the native-tested candidate. The writer receives only the
authored neutral request or a strictly reread neutral JSON document
and the validation receipts. The four workers exercised 28 exact
public or direct publications, eight strict reads, 64 atomic refusals,
all ten stream identities for each archive, and zero runtime input reads
or application launches. The conditional guards cover missing or
altered evidence, locator, creation epoch, D1, and extra readback state.
[Guarded receipt](../measurements/2026/SdkMeasuredOrdinaryRevolveEnds01.json)

The successful file-sink path uses an already-opened empty binary file.
The original measured filesystem destinations remain in custody and
were not replaced in the scoped process proof. The earlier independent
held-out evaluation has its own [record](https://github.com/TryUniCAD/Kit/pull/121).
This delivery adds no new native lifetimes or held-out and FCStd credits.

## Shared queue coverage

The complete suite discovers two focused process tests for Mid Plane,
Two Directions and reversed Two Directions. The measured process checks
all ten logical stream hashes, the strict full and design-only views,
the actual D1 and D2 roles, the directed axis, the sweep interval and
one resolved body. The measured queue process requires the complete SHA-256
to match and checks every publication route. A standalone alternate-compressor
contrast can call the proof worker with `--queue` to verify atomic refusal when
the archive differs despite matching logical streams. That contrast does not
count as measured queue publication. The production compressor and measurement
predicate retain their existing behavior.

The independent process authors three new neutral documents in code
without reading any fixture. These use different rectangular dimensions,
axes and angles, including a Right-plane Mid Plane and a reversed
Right-plane Two Directions profile. The full and design-only readers
retain each actual selection, angular driver and creator. An independent
calculation checks the body volume and area and all eight signed cap
corners. The typed serializer provides malformed contrast archives
with an unexpected Mid Plane secondary end, a shared Two Directions
display, and two distinct angle displays that share one persistent
dimension identifier. Both strict views refuse each applicable
contrast. The public writer also refuses each unmeasured document.
The parser continues to use the typed graph and geometry, independent
of the measured publication digests.
[Measured queue process](../../../tests/Convert/Solidworks/RevolveEnds/RevolveEndTests.py)
· [Independent reader process](../../../tests/Convert/Solidworks/RevolveEnds/RevStructTests.py)

## Native-saved reader boundary

Six immutable SOLIDWORKS 2026 originals and independently edited
derivatives came from the earlier disclosed authoring and Mid Plane
recovery. Their exact SDK process tests consume Config-0 with map
counter 109 in every case. The linked reader then refuses
`moLinkedAtomIdNode_c` schema 1 in `Contents/CMgr`, before it reaches
ResolvedFeatures or either end display. This identifies the first
missing native-saved owner without extending the cold path. The audit
binds each source hash to the appropriate original or derivative
reopen receipt from the prior healthy native controls.

```sh
python3.14 -I -B re/tooling/sw2026/revolve/AuditSavedRevEndBounds.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

Earlier redacted aggregate evidence records two successful Two
Directions parity pairs and three individual passes in the mixed
held-out batch. The mixed batch remained failed and qualified zero
cases overall. The current reader controls add independent
structural evidence and a precise saved-source limit. Native
qualification of new outputs and broader saved-source recovery
remain pending.
[Prior mixed held-out receipt](https://github.com/TryUniCAD/Kit/blob/0e8673133c0c82152a80acab9b502b1a3990e329/re/solidworks/measurements/2026/SdkOrdinaryRevolveEndHeldout01.json)
· [Earlier Two Directions parity](https://github.com/TryUniCAD/Kit/blob/0e8673133c0c82152a80acab9b502b1a3990e329/re/solidworks/measurements/2026/SdkTwoDirectionRevolvePublicParity01.json)
· [Guarded review evidence](../measurements/2026/SdkRevolveEndReview01.json)

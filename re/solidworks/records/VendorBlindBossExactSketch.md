# Preserve exact SI sketch coordinates with millimetre display

The research request contains `schema`, a typed `document` with metre geometry, and `display_units` set to `mm`. D1 and the linked forward blind extrusion carry one typed metre value. Profile lines are directed and share endpoints bit for bit. The ordinary Front support has a zero origin and identity axes. The request has no native slots or retained source data.

The optional `produce` command uses the disclosed Author04 baseline from the existing source evidence. It requires an unmodified PR #121 checkout at `c0a401a607759fb0c2589647c2a22af65ebb7ce1` and the original authoring record. It reruns the [directed body ownership proof](VendorBlindBossSourceAdmission.md#active-body-ownership-at-the-reader-dependency), compares every typed endpoint with the independent API record, and checks the authored millimetre profile before constructing the metre request. This baseline comparison covered 16 XY words and eight zero Z coordinates. The command keeps source custody in its report.

```powershell
python -I -B re/solidworks/EncoderBoundary/ExactSketchIntent.py produce --authored re/solidworks/measurements/2026/EncoderRoundTrip/Requests/BaselineReconstruction.json --source-record <original-author-record> --dependency-root <clean-pr121-checkout> --request <new-si-request.json>
python -I -B re/solidworks/EncoderBoundary/ExactSketchIntent.py generate --request <si-request.json> --locator 'C:\KitEncoderRoundTrip\reconstruction.SLDPRT' --epoch 1785626030 --output <new-output-directory>
```

The `generate` command has no native source argument. Use the same command with the [independently authored five-line request](../measurements/2026/EncoderRoundTrip/Requests/ExactSketchAsymmetric.json) to exercise generation without running the producer. Keep the explicit locator and write epoch to reproduce the recorded archive digests. Both requests use the name `reconstruction`.

The replay projects the SI coordinates once. A transient physically converted millimetre view passes the existing validation and supplies millimetre display intent to the ordinary constructor. Native sketch points come from the SI plan. The independent typed archive read checks the point words, endpoint references, D1 and the document MMGS and analysis MKS tables. Strict SDK readback checks one solid, its face rings, counts, bounds and volume.

Two of the four-line case's XY words and three of the five-line case's lack an exact millimetre inverse. The offline checks cover these words and the signed-zero and display-unit refusals. The five-line case is an authored feasibility contrast. Native acceptance, broader source geometry, and whole-source conversion remain open. [Digest-bound evidence](../measurements/2026/VendorBlindBossExactSketch.json)

## Verified native sketch

The exact offline baseline and five-line archives were opened in fresh SOLIDWORKS processes. Their native ordered XY words, zero Z values, D1 and shared endpoint alias relationships matched the corresponding independently authored controls. The five-line native reference was authored independently from the same semantic SI intent with the application API, then opened in a separate process before the generated file was measured.

| Fresh process | Active seconds |
| --- | ---: |
| Stock before | 12.774 |
| Generated baseline | 11.034 |
| Independent five-line authoring | 11.069 |
| Five-line reference reopen | 10.795 |
| Generated five-line candidate | 10.973 |
| Baseline SaveAs | 11.268 |
| Baseline read-only reopen | 11.082 |
| Stock after | 11.210 |

All eight positively owned lifetimes closed normally. The unchanged native baseline SaveAs and fresh reopen kept the exact XY words, endpoint aliases and D1. The pinned source reader confirmed the saved archive fields independently. The native source and generated files retain distinct configuration names, display state and view ownership, global plane visibility and full unit-format arrays. [Measured lifecycle and exact limits](VendorBlindBossNativeSketchProof.json)

Retrieve the private evidence package under `D:/KitRuns/EncoderSwBossRea20261125/ExactSketchIntent/NativeEvidenceCompanion01/`. Verify the archive and private manifest SHA-256 values recorded in the compact evidence before extracting to an unused private directory. Verify each member with the manifest. The novel reference and its authored shape provide an independent measurement. The installed template is recorded by identity only. Native files and logs contain machine metadata and stay private.

The two measured cases establish exact SI geometry and D1 on the tested build, with the baseline save and reopen. Unseen geometry, basic display settings, complete ordinary source admission and public SDK publication retain their separate requirements.

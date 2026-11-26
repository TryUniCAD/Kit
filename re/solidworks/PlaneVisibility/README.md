# Offline document plane-display comparison

This comparison does not qualify a plane-visibility field or a native writer.
It retains the production Definition refusal and all observed session differences.

## Scope and ownership

This is the A12b offline plane-display discovery comparison, owned by the SOLIDWORKS boundary worker.
It is separate from the Top annotation proof, display-state naming, PR #121's serializers and production source admission.
The implementation starts from `42467da3728d8709f56d01f64b05f45f23560d61`.
The integration owner controls the delivery register and PR.
No push or new PR is part of this tranche.

`CompareCapture.py` reuses the SDK container, complete typed Config-0 reader/writer, Definition schema reader and the research output-manifest validator.
It requires exact source SHA-256 values, format 4 and generation 19000.
Config-0 must re-emit exactly before its typed inventory is recorded.
The ordinary Definition reader runs independently and its actual outcome remains visible.
The separate schema-only path uses the existing `ModelDefContext`, `GraphReader` and `ReadBodyMut`, canonical tags and complete stream consumption.
It deliberately does not call `CheckDefScope` and does not establish production admission.
No production guard is changed.

The inventory preserves every reached typed field, class/object owner, alias, map slot and node extent.
It stores binary64 values as hexadecimal strings and hashes byte fields and text instead of publishing their contents.
Comparison uses exact paths and values without identity remapping, field masks or semantic inference.
The full inventories and comparisons stay in ignored output; the tracked ledger binds their exact hashes and lengths.

## Run

Use an unused research output directory:

```powershell
python -B re/solidworks/PlaneVisibility/CompareCapture.py --before $NoOp --before-sha256 a8bb1aae363e0dbaead760803f7e9e1928ebdbf0d6fa400e714e0c9c3c39420d --after $Toggled --after-sha256 c076af4a2397f4b58456196f25f91feac791ca11b5e21b8d591f51820996e159 --purpose controlled_toggle --receipt $FinalReceipt --receipt-sha256 84e928b8f611d107fccb4e2b9604e6503e1ef8ec6f53c2c8013b66f2d77836cf --preflight-receipt $StoppedReceipt --preflight-sha256 043b23d558141202f8fd2571c7a32dc793905ed736766a8742c50e201f9d5a75 --output .rescratch/PlaneComparison
```

The final receipt must bind the exact stopped receipt, common plan and executable.
The command rehashes the private phase records, requests, request sources and snapshots, checks exact reused-phase fields and verifies matching normal exits.
The stopped failure remains false in the output; the continuation does not rewrite it.
The receipt proves capture custody only, not writer acceptance.
`diagnostic` and `noise` purposes retain their weaker scope.

To regenerate the compact ledger from the four named comparison folders, repeated toggle report and recorded process checks:

```powershell
python -B re/solidworks/PlaneVisibility/SummarizeComparisons.py --directory .rescratch/CommittedPlaneProof --output .rescratch/PlaneComparisonProof.json
```

## Actual offline evidence

[ComparisonProof.json](ComparisonProof.json) records five fresh Python 3.14.6 comparison processes, two guarded process refusals and the SDK source-tree fingerprint.
The two toggle processes produced identical complete reports with SHA-256 `148b4ea156c675faa46f90dffe751c6031cba46652dc1c873bf02d432c035663`.
Wrong source identity and a valid but unrelated preflight receipt each exited 1 before creating an output directory.
No CAD application or model service was called.

| Pair | Changed clear streams | Changed Config rows | Changed schema-only Definition rows | Map equality |
| --- | ---: | ---: | ---: | --- |
| Old vendor versus native-saved Kit diagnostic | 27 | 781 | 465 | Both differ |
| Prior warmed no-op | 9 | 53 | 0 | Both equal |
| Current same-session no-op | 4 | 53 | 0 | Both equal |
| Current cross-session toggle | 21 | 109 | 84 | Both equal |

The same-session no-op keeps both observed `fad8` words unchanged at `(1067879674, 1610617865)`.
The toggled archive changes the low word to `1067748602`, an XOR of `0x00020000`, while the high word stays unchanged.
This is a measured typed-field difference, not a bit-17 meaning or serializer rule established by this comparison.
The toggle crosses authoring lifetimes and also changes other Definition fields and 21 streams.
All strict Definition reads still refuse the alternate renderer profile.
Complete schema consumption is not portable semantic qualification.

## Remaining authority and proposed contrast

Loader, secondary-mask and concrete save/load authority remain separately owned research.
This tranche has not independently established that authority and does not infer a mapping from API preference number 5 to a filed bit.
No reserved holdout was read.

A proposed selective contrast would use a separately authored model, one warmed process and the same working pathname throughout: unchanged save while true, toggle false and save, unchanged save while false, then inverse toggle true and save.
Measure both independent document-level getters and all non-target state around each step.
Keep that comparison separate from another fresh read-only reopen and from frozen held-out validation.
This proposal has not been executed here.
The sole oracle has since reported a same-process inverse capture; it is available for separate offline corroboration and is not part of this frozen four-pair ledger or an independently authored held-out geometry.

The next exit requires unconfounded contrasts plus the actual loader and save/load ownership proof before a field rule can be qualified.
Source admission, neutral intent, generative emission and fresh native acceptance retain separate exits.
Both acceptance flags remain false.

[Exact-build field ownership and generated plane request](FieldAndWriter.md)

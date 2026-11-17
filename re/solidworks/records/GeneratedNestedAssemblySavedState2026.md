# Persisted typed state after the first generated nested assembly edit

The first generated three-file hierarchy passed native open, rebuild, the driving leaf-depth edit, dependency-ordered saves, fresh reopen and both controls in four distinct SOLIDWORKS processes. The independent typed audit read the immutable generated originals and their actual saved derivatives. All 36 scoped stream read/store checks passed, including Config-0 and ResolvedFeatures as one continuous object map. The saved depth is `0.0103 m`. [Typed comparison receipt](../measurements/2026/GeneratedNestedAssemblySavedState01.json) · [Original trial protocol](GeneratedNestedAssemblyNativeProtocol2026.md)

The native combined result has SHA-256 `539cb901df420671788475640ad5f097d673c48027a2754bea1e01396e908158` and binds the generated writer revision `aa245b58e0dc9857f07e68aafa9727925ec52386`. The audit independently checks its immutable packet digest, the three saved statuses `[true,0,0]`, each saved file's hash and length, and the hashes observed on fresh reopen. The six scoped streams per file are Config-0, ResolvedFeatures, CMgr, CMgrHdr2, ModelHeader and Header2.

| Definition | Original header update | Saved header update | Original geometry/transform | Saved geometry/transform |
| --- | ---: | ---: | --- | --- |
| LinkPlate | 101 | 207 | 101 / 101 | 107 / 101 |
| OffsetModule | 101 | 107 | 202 / 102 | 210 / 102 |
| TiltFrame | 101 | 105 | 303 / 102 | 313 / 102 |

Each configuration's `f860`, its CMgrHdr2 update stamp and its two header update stamps agree. Each parent's reference points to the saved child's header update and modification time and its computed CMgrHdr2 geometry/transform pair. The module's saved geometry stamp is `103 + 107 = 210`, and the root's is `103 + 210 = 313`. Each direct transform stamp remains `102`. Directory file/save times match the saved child self record and saved CMgrHdr2. The direct external object identity survives the Config-0 to ResolvedFeatures map handoff.

The saved Config-0 part model contains the real generated sketch and extrusion history. The extrusion's `moEndSpec_c` retains its forward blind, one-direction state. The active `D1` length parameter changes from `0.0068` to `0.0103 m`. Its inactive reverse `D2` stays `0.0068 m`. Both saved occurrence-local bounding boxes match all ten words of their actual saved child-local boxes. The module has one direct reference and one CMgr path. The root has one direct reference and two expanded occurrence paths.

Header component-count copies also record save context. The generated originals store module counts `1/1` and root counts `2/2` in ModelHeader/Header2. The saved module stores `0/0` while its configuration activity stays `1`. The saved root stores `2/3` while its configuration activity stays `2`. Those are independent observed fields in this native lifecycle. The first generated values already passed the measured native trial. [Save-context gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ExternalReferences/NestedSaveHeaderCountsUseDocumentContext.md) · [Construction activity rule](NestedAssemblyHeaderActivity2026.md)

The research codecs still report their provisional context-chain and string-map owners and bounded raw operations. The audit reports these coverage limits alongside byte identity. This comparison supplies disclosed native persistence evidence. Qualification on the sealed source cohort follows the repeated-layout discovery trial.

```sh
python -B re/tooling/sw2026/serial/AuditGeneratedNestedSave.py "$GENERATED_NESTED_TRIAL"
```

The auditor accepts only the first disclosed generated trial and its exact original packet and native result hashes. It writes its sanitized JSON to stdout and leaves native files intact. [Auditor](../../tooling/sw2026/serial/AuditGeneratedNestedSave.py)

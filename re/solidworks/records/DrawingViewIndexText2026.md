# Drawing view index configuration text in SOLIDWORKS 2026

Task `PR121-DRAWING-VIEW-INDEX-TEXT`; owner `configuration_header`; delivery PR #121. This is a narrow typed reader correction, with host process evidence pending independent root integration. Its exit condition is an exact one-file helper delta, unchanged field/identity guards, and independently replayed raw and public-path preservation. It does not complete the broader drawing conversion goal.

## Existing owner proof

The [reference-chain grammar](DrawingReferenceChainArchive2026.md) and [component-profile archive](DrawingComponentProfileArchive2026.md) bind native owners. The [origin-linkage proof](DrawingOriginProfileLinkage2026.md) already establishes that the disclosed original displays target the actual child origin, and [portable origin projection](DrawingOriginPortableProjection2026.md) covers the constrained construction join. Neither rule is reintroduced or widened here. The pinned `sldmodu.dll` is SHA256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`, from SOLIDWORKS 2026 SP05.2. No binary or proprietary listing accompanies this change.

## Actual representation mismatch

`moAbsoluteView.f5d8` reaches `moReferenceInternal_c`; its `f3c0` is the embedded `moReferencedConfiguration_c`. The existing schema describes `f08` as text and `f10` as the signed selected-configuration local ID. Normal `ReadNamedDef` decodes `f08` to a plain Python `str`. The fresh `MakeFileConfig` constructor represents the same modeled text as `CStringValue`.

`ReadViewIndex` accepted only the constructor wrapper. It rejected the normal decoded selector on all six disclosed archive states, including native original Right/Top views, native Front, generated Front, and both native-saved Front derivatives. The existing wrapped form succeeded on the identical actual graph. The correction unwraps `CStringValue` only when present, then requires an exact `str` and applies the original text validator. No field, alias, archive map or counter is modified.

The actual file-kind, absolute Windows path, `.sldprt` suffix, path-stem/title agreement and selected configuration-ID predicates remain unchanged. All six header directories already have the matching physical basename. A title-versus-basename defect is not established by this cohort and no such guard was relaxed. Both original drawings reference the same child hash; they are two view cases, not independent child designs.

## Measured host boundary

[The sanitized process receipt](../measurements/2026/DrawingViewIndexTextProcess01.json) binds 56 fresh SDK processes: six archive states in baseline/candidate pairs, plus 11 malformed variants on two different actual archives in both variants. All complete Definition streams reproduce their input bytes before and after index observation, and all map counters remain unchanged. The candidate accepts the actual decoded index and exactly matches the existing wrapped-constructor index on all six positives. Both baseline and candidate reject every malformed variant.

The paired ordinary `open_document(..., source_format="solidworks.slddrw", strict=False)` observations retain identical public drawing semantics, diagnostics and unprojected owners. `strict=True` remains refused. The existing unknown populated-profile flag guard remains active. No additional model file open, stat or lstat is permitted under the worker guard. Inputs and the 4,666-file source manifest remain unchanged during the process run. No CAD application is launched and no CAD file is generated.

Black, Ruff and strict Mypy passed on the exact proposed module. Pyright and steering were not run on the private in-memory module. The first Mypy invocation failed at argument selection; the first successful invocation then wrote ignored `.mypy_cache` files in the shared checkout. No SDK source or Git/index file changed, and no cache was deleted. The final successful Mypy run used an explicit private cache. This exception is retained separately from the earlier process proof's source-custody statement.

## Integration and remaining limits

The stageable delivery contains a unified source delta, independent research methods, this record, the receipt, a change entry and a patch to the existing representation gotcha. It contains no full SDK module clone, source archive, model payload or vendor listing. The private controller uses the already-disclosed host corpus locations and verifies exact hashes; it is an evidence replay, not a portable public CLI. Run it before applying the physical source delta, because both variants require the old module hash and the candidate overlays only that import in memory.

No new public writer or strict drawing reader is registered. Detailing edges, occurrence colours and profile displays remain unprojected wherever they were before this correction. The original full-source writer refusal and earlier failed held-out verdicts are unchanged. This is disclosed regression evidence with zero new original held-out credit.

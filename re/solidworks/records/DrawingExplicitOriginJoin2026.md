# Explicit child resolution for drawing origin displays

Task `B04-SW2026-DRAWING-ORIGIN-PROFILE/explicit-child-join`, owners `configuration_header` and `/root`, delivery PR #121. The research component resolves the actual child origin and sketch from two disclosed drawings. Public strict drawing reading and complete original-source conversion remain open.

## Existing rule and current missing boundary

The [origin-linkage proof](DrawingOriginProfileLinkage2026.md) identifies the native target, and the [portable projection](DrawingOriginPortableProjection2026.md) records its source owners. The constructor's `CheckOriginLink` consumes fresh `LinkedDrawFile` and `PartCandidate` owners. Public `ReadDrawing` currently receives the drawing bytes for its layout inspection. The retained `NamedRead.ProfileDisplays` still require an independent child for portable projection.

Both disclosed original Right/Top drawings retain a component-profile reference to the actual child origin. Their sole public child sketch is the different ordinary sketch. Selecting that sketch by name, archive-map index, or an ID shift would change ownership. `ReadOriginJoin` instead follows the real display/folder/view/reference chain, then the wrapper's positive persistent ID and the actual child creation-log epoch. It returns the same native origin and its same `sgSketch` object. No portable ID or displayed geometry is fabricated.

## Typed byte-only interface

`ReadOriginChild` accepts caller-supplied child bytes, an absolute declared Windows `.sldprt` reference path and an independently resolved expected SHA256. It checks that binding and decodes complete ordinary Config-0 plus CMgr and Resolved owners. It never follows the archived path on disk. `ReadOriginJoin` consumes the actual retained `ProfileDisplay` and that explicit `OriginChild`. It rechecks folder/view publication, ordinary component flags, the sole external chain, the actual view-internal reference, selected CMgr aliases, child self configuration, positive origin ID and source-owned creation epoch.

The drawing does not contain a trusted payload digest. The caller must establish resolution independently, for example through an explicit immutable bundle association already measured against the native child. Merely matching names or self paths cannot authenticate a replacement child. The archived child's self model title differs from the drawing directory's physical basename in these real inputs; that is retained as separate source state. The actual declared reference path must match the explicit resolver path, while the child's independent historical self title/path are not substituted for it.

The reference-chain `f24` is its bounded ordinary selector. Its `f20` is a retained acquisition count, not a feature ID and not an emptiness predicate. The two benign count controls preserve the exact same resolved origin without changing that counter in the source graph. The component's runtime handle word is likewise not used for child feature lookup. Special chain selectors, auxiliary display state, contextual paths, negative-ID remapping and other profile target classes remain refused.

## Host proof and retained boundaries

[The final receipt](../measurements/2026/DrawingExplicitOriginJoinProcess01.json) binds 48 fresh SDK processes: two exact original states, two benign counter controls, and 22 rejection variants on each original. All five complete streams reproduce their original bytes before and after observation: drawing Definition, child ModelHeader, CMgr, Config-0 and Resolved. Every child strict public read passes. Every partial public drawing read preserves its drawing semantics, zero public sketches, layout diagnostic and original strict refusal. No additional model file open, stat or lstat is permitted under the runtime guard.

Both original views use one identical child payload. This proves two orientation/ownership states, not independent child-design generalization. The actual origin and ordinary sketch remain distinct. The existing `drawing.detailing_edges`, `drawing.occurrence_colours` and `drawing.profile_displays` markers are unchanged. The component is not connected to the public adapter, does not clear a marker and does not enable a writer. It supplies an internal identity boundary for a future explicit bundle projection. Portable displayed geometry and full detailing/appearance semantics still need their own implementation and qualification.

Black, Ruff, strict Mypy and strict Pyright passed on the five prototype modules before research publication. An independent replay reproduced the original proof digest. The published runner uses a caller-provided disclosed root and preserves the original candidate logic in the research tree. The integrated run repeats the same guarded comparisons.

```sh
python -I -B re/tooling/sw2026/drawing_origins/RunOriginReplay01.py \
  --root /absolute/path/to/Kit \
  --disclosed-root /absolute/path/to/disclosed/originals \
  --output /absolute/path/to/new-output
```

The original-module SHA256 remains `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. A target-free REA resource inventory independently rehashed that file; it did not create a native session. The existing native getter/class proof is reused with its complete addresses and source fingerprints. No proprietary code, binary or listing is distributed.

## Historic ZIP save interval

The earlier [property-save brackets](../measurements/2026/DrawingBlankPropertySaveBracketsNative01.json) saw both general-property and summary returns, then an armed but undelivered generated SOLIDWORKS-bag return. That observation does not identify a C++ exception or prove an asynchronous route. The finite source graph already locates a synchronous XML reparse check at `sldmfcu 0x3c892689..0x3c89269a` and the file-exception path at `0x3c892755`, bound to module SHA256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`. Its exact runtime branch remains unmeasured.

The [per-tree prefix correction](DrawingPropertyPrefix2026.md) subsequently passed ten blank phases and [eight linked-front phases](DrawingFrontPropertyPrefix2026.md). The generic DOM replay independently reproduces the namespace mechanism. Those results repair that historical save failure without retroactively turning breakpoint nondelivery into an observed throw. A new old-path native trace is not needed to establish the present public reader gap. If an exact ZIP-internal attribution is later required, the smallest additional observation is the signed MSXML load result plus its actual parse-result output at that reparse gate, with qualified control return and cleanup; no stack-output address may be guessed from the old receipt.

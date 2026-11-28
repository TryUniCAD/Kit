# Native tree and pose parity for generated parts

## Problem and resulting behavior

The research composer previously emitted a top-level notes-area node instead of
the ordinary markup class. Native loading added the missing markup folder,
leaving an extra node and a different order. Authored empty-material captions
also changed on fresh reopening.

The new ordinary folder map emits the concrete markup class and explicit
standard English captions through the shared generative graph. Two independent
pre-implementation sources now match the generated parts through rebuilding,
radius/depth edits, saving and edited fresh reopening. The old explicit notes-area
input form and its historical output hashes remain intact.

## Measurements

The [paired receipt](../../../../../re/solidworks/measurements/2026/TreeParityInspection01.json)
records:

- Two independent cases, six source phases and six generated-candidate phases.
- Fourteen distinct process-creation identities, including healthy controls.
- All 840 numeric checks pass and all 840 six-significant-digit text comparisons match.
- All 440 pose comparisons are exactly equal.
- Twenty generated/source ordered-tree comparisons, plus two source/original-API comparisons, pass.
- Every tree has the same 25 nodes, names, types, parents and suppression states.
- All forty scene observations have one visible solid body.
- Volume, area, centre of mass, principal sketch frame, fixed-centre relation and driving dimensions pass before and after edits.
- Maximum nonzero relative error is `9.372177682159633e-16`; zero targets are exact.
- Source, generated input, control and private-observation hashes remain unchanged.
- Postflight has no CAD process, and all licensing process IDs are unchanged.

The frozen writer is `d5019da136433cf3b07dd8c53ee4a708950ad353`.
Its two predictions passed sixteen complete archive comparisons in the
[remote prediction receipt](../../../../../re/solidworks/measurements/2026/TreeHeldoutProcessesE727.json).
That receipt was committed before native reference access. The observer is
`f6d146269130c378672aca97b13812653f61e678`; it calls no view setter and measures
the source's edited pose independently instead of replacing it with a constant.

## Scope and limits

This qualifies the bounded ordinary-English tree/pose rung for these two blind
circle bosses. The failed earlier mixed-end source pair remains failed and
ineligible. The result does not establish arbitrary folder edits, locale
selection, complete feature coverage, materials/appearance parity, or pixel-level
viewport equality. Vendor-saved derivatives are not new generated outputs.

The public adapter remains read-only. Production conversion acceptance remains
zero parts and zero assemblies. No local tests, writer or codec execution ran;
generation and archive checks ran in remote CI, and native measurements ran in
the reserved Windows VM through the committed COM observer.

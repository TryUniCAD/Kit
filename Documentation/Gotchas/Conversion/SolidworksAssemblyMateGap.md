# Assembly mate generation gap

## Expectation

A neutral assembly with component instances and mates can be written from scratch as a
native SOLIDWORKS assembly without a template, and the writer can prove the
`assembly_mates` capability.

## Actual behavior

From-scratch assembly generation proves `assemblies` and `component_documents`, bundles
the referenced component parts, and can be application-usable and vendor-loadable when
the assembly has no mates. Mates are different: the capability proof in `AsmCaps` only
adds `assembly_mates` when the encoding carries complete saved mate streams. A synthetic
assembly with a coincident mate still reports `assembly_mates` as
`writer_unimplemented`, so `write_document(..., allow_carrier=False)` raises
`ApplicationUsabilityError`.

Template-backed assemblies are unaffected. Reading and rewriting a 91 KB repository
example (`re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/ENSAMBLAJE
DE SEGURO DE ARBOL DE LEVAS.SLDASM`) with three mates (concentric, native, coincident)
and two external parts produced `native-template`, `native_self_contained True`,
`referenced_files_written 2`, vendor-loadable and application-usable output, and the
re-read assembly equalled the source.

## Workaround

Do not claim mate parity for from-scratch assemblies. Either keep the source assembly so
its saved mate records travel through the template path, or write without mates and
expect `assembly_mates` to remain unproven. Recovering native mate record generation,
then validating it in the SOLIDWORKS oracle, is the prerequisite for closing the gap.

## Evidence

`tests/convert/solidworks/assembly/SolidworksAssemblyEnvelopeTests.py` adds
`TestASBBundle`, which writes a from-scratch one-component assembly (no mates), requires
vendor-loadable, application-usable, self-contained output, one bundled `.sldprt`, and a
re-read assembly with one instance and two definitions. The mate rejection is reproduced
by the same fixture with a coincident mate: `unimplemented_capabilities` contains
`assembly_mates`.

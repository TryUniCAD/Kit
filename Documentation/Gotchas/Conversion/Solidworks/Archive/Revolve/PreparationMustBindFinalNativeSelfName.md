# Preparation support must validate the actual native self name

The shared final-path helper validates syntax, target kind and staging/final filename consistency. A Windows final path can still have a basename different from the neutral document's modeled name. The constructor's existing `CheckPartInput` rejects that mismatch, but a support predicate that stops after final-path selection can incorrectly return true.

The first guarded revolve preparation matrix exposed this difference. The wrong-basename case was declared supported while actual construction still refused before publishing bytes. The source and false 31-process result were preserved. The corrected input preparer runs `CheckPartInput` before returning validated input, so both support selection and construction enforce the same document/name/configuration/path ownership.

Keep target existence and transactional writes with the actual I/O layer. The internal preparer must not read a destination to validate its semantic identity. Named streams require an explicit final destination and retain that exact encoded self path.

[Measured correction and frozen evidence](../../../../../../re/solidworks/records/SdkRevolvePreparation2026.md) · [Process receipt](../../../../../../re/solidworks/measurements/2026/SdkRevolvePreparationProcess01.json)

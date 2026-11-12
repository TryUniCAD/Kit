# Binary Fusion geometry needs the binary import route

`createSMTImportOptions` validates the `.smt` extension and selects a text parser. Passing a generated `.smb` fails option creation; renaming the same binary bytes to `.smt` passes extension validation but fails document import. Neither outcome demonstrates malformed binary geometry.

The installed API documents `TemporaryBRepManager.createFromFile` as supporting SMT, SMB, SAT and SAB. The unchanged generated `.smb` succeeded through that API, produced the expected cylinder, and retained its geometry after insertion into a direct design, native save and reopen.

The temporary body's `physicalProperties.centerOfMass` returned zero even though its volume and bounding box were correct. The same body reported the correct center after insertion into a persistent native design, and after reopening. Check full physical properties in that context; retain the temporary observation rather than assuming every temporary-property value is authoritative.

The failed binary-as-text import also left an empty, unmodified `Untitled` document despite raising before returning a document handle. Cleanup verified that exact empty state before closing it. Import-oracle cleanup must account for partially created documents without touching unrelated documents.

Evidence: [failed text route](../../../re/Fusion/LocalOracle/Brep/BinarySmtAcceptance.json), [successful binary route](../../../re/Fusion/LocalOracle/Brep/BinaryTemporaryAcceptance.json), [temporary center discrepancy](../../../re/Fusion/LocalOracle/Brep/BinaryTemporaryCenterFailure.json), [cleanup](../../../re/Fusion/LocalOracle/Brep/FailedImportCleanup.json), and [native dispatch disassembly](../../../re/Fusion/Reconstruction/BinaryImport/StaticEvidence.json).

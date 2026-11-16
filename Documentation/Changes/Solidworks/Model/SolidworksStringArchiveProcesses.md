# String framing through complete modeled archives

The research command `re/tooling/sw2026/serial/StringCorpus.py` checks string framing through eight complete modeled archives in two separate Python processes. The existing native-format PR CI runs its process test and retains reports, command logs and reduced research containers beneath `SwResearchOutput/SourceParser/Curve/Strings`.

`prepare OUTPUT` requires a new directory outside the checkout. `verify OUTPUT` requires its completed preparation report and a fresh interpreter. Verification belongs in remote CI; local execution remains prohibited by repository policy.

The input is the immutable public rectangle control from the prepared discovery manifest. The command edits only `Header2` → `moStamp_c` → `f20`, the documented revision comment. It discovers the actual owner and frame boundary from the parsed model. Every emitted stream is regenerated through its actual model serializer. Configuration storage computes the map seed used by resolved-feature storage. The container builder receives only those generated results, without a source envelope, template or saved-stream passthrough.

The reduced containers contain `Contents/CMgr`, `Contents/Config-0`, `Contents/Config-0-ModelHeader`, `Contents/Config-0-ResolvedFeatures`, `Contents/Definition`, `_MO_VERSION_19000/Biography`, `_MO_VERSION_19000/History` and `Header2`. Other source streams are omitted and inventoried by name, length and hash. These containers are archive-compatibility fixtures, not complete native CAD documents or neutral-model writer outputs.

Ten positive cases cover Unicode length boundaries at 254/255 and 65,533/65,534 UTF-16 units, non-BMP text, an unpaired surrogate, empty Unicode and ANSI frames, and explicit ANSI wire bytes. Each process reruns the unchanged source baseline. The checker requires complete primary and linked parsing, exact model graph and map fingerprints, unchanged neighboring fields, complete stream restorage, and identical implementation/source hashes. It retains the configuration seed's real origin rather than relabeling inherited objects as resolved-local.

Three explicitly tainted negative controls replace only the dynamically located string frame of an already model-regenerated header. Repeated Unicode markers and reserved Unicode/ANSI double-word lengths must fail at that exact field before storage. Each tainted header records both the pristine model-store hash and its corrupted emitted hash. No negative fixture earns writer or native acceptance credit.

The reports use `kit.sw2026.cstring-process.v2`. They state that no held-out payload was read, no donor template or saved-stream passthrough was used, and no complete native document, writer output, native acceptance or native field-length acceptance is established. ANSI remains reversible source-byte text, without semantic code-page conversion. Long-string and lone-surrogate acceptance in SOLIDWORKS is outside this check.

The command and process test passed static source, AST and formatting review. Remote execution of this new check is pending publication. The existing shared object/map implementation passed all current PR CI on source `9d7209d515d6d7c6fafa461ae7dad917c97f8226`; that result does not establish this newly added check.

See the [typed primitives](SolidworksArchiveStrings.md), [2026 framing record](../../../../re/solidworks/records/CStringArchive2026.md), [metadata owner](../../../../re/solidworks/records/MetadataConstruction2026.md), [encoding gotcha](../../../Gotchas/Conversion/Solidworks/Archive/CStringEncodingAndLengthUnits.md), and [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md).

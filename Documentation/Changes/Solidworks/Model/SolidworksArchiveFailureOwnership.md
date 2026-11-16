# Archive failure ownership diagnostics

Tracked research archive loads now attach the innermost active schema path, operation path, concrete object class, cursor, remaining length and scalar/count state to an `ArchiveError` that has no existing details. The original exception still propagates. Existing custom details remain unchanged. These diagnostics capture no CString contents or opaque source spans and never supply a writer value.

The saved-circle reader process retains both full primary and linked reports on failure. Its first remote run at `17e9e9ef6` checked all 54 requested archives, but six Config-0 loads and their six linked dependents failed with end-of-stream integer reads; the other 42 archives passed. No semantic pass is claimed. The new diagnostics locate the failed typed owner without truncating an input, skipping a field or relaxing a gate.

The semantic targets now remain those independently checked against the neutral generator receipt and native edit factors; redundant fixed feature-name assignments were removed.

Verification at introduction: static source/AST inspection only. All archive-schema and process execution remains in remote CI. Native body/edit evidence, saved archive acceptance, complete family acceptance and production writing remain separate facts.

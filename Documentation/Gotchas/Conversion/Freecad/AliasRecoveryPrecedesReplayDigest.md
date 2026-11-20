# Spreadsheet alias recovery must run before the replay digest

Native FCStd reads recover [spreadsheet alias dependencies](SpreadsheetAliasesAreNotParameterIds.md) after decoding.
Exact native replay compares a stored semantic digest with the digest of a fresh native parse.
Both digests must be computed from documents that passed through the same recovery.

## Expectation

Alias recovery could run after the native read returns, as one more read-path step.

## Actual behaviour

`ReadNativeArc` stamps the replay digest with `AnnotateNative` inside the read.
A later `RecoverAlias` call changed the parameters and capabilities after the stamp.
The stored digest then no longer matched the document, so unchanged archives stopped replaying exactly.
Running recovery only on the replay side changed linked child documents that the read side left unchanged.
Linked reads repeated, an unchanged linked bundle lost its exact round trip and component requirements were omitted.

`RecoverAlias` also widened capabilities with `InferCaps` when a document had no spreadsheet alias.
That change alone altered digests for documents without spreadsheets.

## Workaround

`ReadNativeArc` runs `RecoverAlias` on every decoded document before it stamps or caches the result.
The read path and every replay reparse share this one call, so both sides of a digest comparison see the same document.
`RecoverAlias` returns the document unchanged when it finds no alias and no issue.

## Evidence

The merge of `main` into the automation branch exposed the problem.
`tests/Convert/Freecad/FreecadTests.py::TestLinkedReads`, `TestRestoreLink` and `TestNonportable` failed with recovery outside the read and passed with the workaround.
`tests/Research/Archives/FreeCadAliases/NativeAliasTests.py` and `tests/Research/Archives/FreeCadTwoLengthBindingTests.py` pass with the workaround.

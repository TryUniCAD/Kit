# Static review can resolve a sibling script module incorrectly

Direct script execution resolves imports from that script's directory first.
The review context builder imports its adjacent `CollectFiles.py`, whose function accepts files and revision evidence.
GitHub Code Quality instead linked that call to the unrelated four-argument collector under `DiffBreakdown` on PR #399.
Adding those arguments would break the actual runtime call.

Verify the imported callable's source path and signature with the review script directory first on `sys.path`.
That inspection resolved `.github/scripts/Review/CollectFiles.py` and its two-argument signature.
The same false positive recurred on PR #402.
The review collector now has the unique module and callable name `ReviewSources` to remove that ambiguity.
Its two-argument contract and behavior remain unchanged; no analyzer rule is disabled.
See [the original finding](https://github.com/TryUniCAD/Kit/pull/399#discussion_r4727406730).

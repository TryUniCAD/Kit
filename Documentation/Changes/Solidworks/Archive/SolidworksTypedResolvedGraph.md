# Typed ordinary SOLIDWORKS resolved graph

The SDK reads and serializes the ordinary version-19000 `ResolvedFeatures`
graph. It extends the actual Config map, retains inherited object identities
and obtains the model context from the independent CMgr. The context determines
whether a direct part-body mapping record follows the feature roots.

`ReadResolvedMut`, `WriteResolMut` and `ResolvedGraph` live under
`src/convert/adapters/solidworks/Archive/Resolved/`. The research entry point
delegates to them through `ResolvedBridge` and reports an unadmitted diagnostic
outside the SDK profile. Full linked semantic admission remains open.

The source layouts add 109 native owner and helper grammars. Shared field
expressions encode the mapped native conditions. Packed display arrays decode and
encode individual binary64 parameters. Schema checks use runtime class metadata.
Unknown nonempty generic arrays, unbound classes and residual tails fail closed.

Use unused report paths for the actual process checks:

```sh
PYTHONPATH=src python re/tooling/sw2026/serial/CheckSdkResolved.py INPUT.SLDPRT --report /tmp/UnusedSdkResolved.json --malformed --modeled-edits
PYTHONPATH=src python re/tooling/sw2026/serial/CheckResolvedBridge.py INPUT.SLDPRT --report /tmp/UnusedResolvedBridge.json
```

Twelve disclosed streams pass byte identity and preserve their configuration
map aliases. The processes also pass 72 negative cases, twelve feature-name
edits, twelve complete graph comparisons and a guarded generated pair. The
linked checks pass 36 core streams and six mate lists. The receipt binds the
exact source and input hashes. Native and held-out qualification remain open.
[Verification receipt](../../../../re/solidworks/measurements/2026/SdkResolvedGraph01.json)
[Format ledger](../../../../re/solidworks/records/ResolvedBodyGrammar2026.md)

The [CAD criteria](../../../Reference/Operations/CadSuccessCriteria.md) apply.
See the [empty array](../../../Gotchas/Conversion/Solidworks/Archive/Resolved/EmptyArraysDoNotProveElementGrammar.md)
and [split count](../../../Gotchas/Conversion/Solidworks/Archive/Resolved/SplitCountsKeepCombinedWireOwnership.md)
records for the two field boundaries.

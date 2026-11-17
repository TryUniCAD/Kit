# Typed ordinary SOLIDWORKS configuration graph

The shared SDK archive model now reads and serializes the declared ordinary
version-19000 `Config-0` body graph. Header direct references retain their original
node identities. CMgr remains a separate map-one dependency whose `f658` supplies
the later resolved-body context.

The normal reader adds `solidworks.typed_configuration_graph` metadata with
actual usage, map boundaries, header aliases and the remaining linked dependency.
Existing semantic projection and the read-only adapter registration remain.
`full_linked_graph` and `resolved_body_codec_promoted` remain false. This is a
complete supported stream grammar boundary, not fresh native writer acceptance.

Internal pure-memory APIs are `ReadConfigMut`, `WriteConfigMut`,
`ConfigGraph` and `MakeLinkContext` under
`src/convert/adapters/solidworks/Archive/Config/`. The actual research Config
loader uses them through `ConfigBridge`. Unsupported research profiles retain
an explicit unadmitted diagnostic; production has no research fallback.

Use the real process checks with unused report paths:

```sh
PYTHONPATH=src python re/tooling/sw2026/serial/CheckSdkConfig.py INPUT.SLDPRT --report /tmp/UnusedSdkConfig.json --malformed --modeled-edits
PYTHONPATH=src python re/tooling/sw2026/serial/CheckConfigBridge.py INPUT.SLDPRT --report /tmp/UnusedBridgeConfig.json
```

`CheckSdkConfig` checks literal bytes, aliases and map ownership, rejects malformed
framing/schema/domain cases, and verifies input-dependent name/array writes.
`CheckConfigBridge` compares all decoded fields, aliases, positions and maps
against the existing independent research field reader. The permanent process
regression generates its own neutral part/assembly pair; it adds no vendor CAD
blob.

The parent independently ran the frozen SDK overlay on twelve disclosed files:
12 exact stream comparisons, 72 malformed rejections and 24 modeled edit checks
passed. Both directions exercised 153 body schemas; five separately loaded
header owners complete the original 158-name Config-load dependency union.
Subsequent bridge/integration results are recorded only when actually executed
in the [format ledger](../../../../re/solidworks/records/ConfigBodyGrammar2026.md)
and its bound receipt. No VM or CAD runtime was used for these source checks.

The supported profile rejects other versions, unknown classes, nonordinary
archive paths, inline drawing framing and unread tails. Native runtime schema
zero for `moFeatColorTab_c` is bound directly to the pinned class metadata;
abstract bases are not admitted as concrete objects. Field semantics, unexercised
branches, C10 and full native application acceptance remain unfinished.

See the [runtime-schema gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Configuration/FeatureColorTableRequiresSchemaZero.md),
[cyclic-owner gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Configuration/OccurrenceBacklinksNeedCompletedConfiguration.md),
and [CAD criteria](../../../Reference/Operations/CadSuccessCriteria.md).

The final frozen bridge source also passed all twelve field/alias/position/map
comparisons, the permanent guarded neutral-pair process regression, 36 linked
Config/CMgr/Resolved stream checks and six exact seeded MatesList checks. The
[receipt](../../../../re/solidworks/measurements/2026/SdkConfigGraph01.json)
retains exact source/input/report identities. A generic MatesList-plan diagnostic
is retained as a failure separately; it is not counted among the 42 successful
linked stream checks.

# Read and serialize typed SOLIDWORKS configuration managers

The ordinary version-19000 configuration-manager codec now lives in the SDK.
It reads one `moConfigurationMgr_c` root from `Contents/CMgr` into the existing
typed archive nodes. Its independent object map starts at 1. The same grammar
serializes those nodes and computes tags, object slots, string lengths and row
counts from the graph.

The first profile covers 16 concrete schema-1 runtime classes and 46 reached
native owner and helper schemas. Unknown classes, unsupported embedded paths,
other versions and unproved external-reference profiles fail explicitly.
The codec contains field order, primitive kinds and native control conditions.
It contains no saved field values, per-file operations, opaque payload fallback,
research imports or CAD dependency.

Normal part and assembly reads expose the result in
`metadata["solidworks.typed_configuration_manager"]`. A complete result includes
configuration names, stored comments, alternate names, feature descriptions,
native IDs, actual selected-pointer identities, grammar usage and the manager's
`f658` resolved-body mapping context. The reader preserves the existing semantic
projection on unsupported manager profiles and adds a diagnostic. The metadata
records `full_linked_graph: false` throughout this tranche.

The research CMgr plan and resolved-stream context loader use this SDK codec.
The generic node factory retains their existing `Obj` identities. For another
research profile, the previous typed research reader remains available with an
explicit `shared_schema_usage` record whose `admitted` value is false. Actual
SDK usage is reported separately from research execution, with independent load
and store completion. Missing or malformed admitted fields never fall back to
opaque bytes.

Run the real component check with an unused report path:

```sh
PYTHONPATH=src python re/tooling/sw2026/serial/CheckSdkCmgr.py part.SLDPRT assembly.SLDASM --report /tmp/CmgrReport.json
```

Twelve disclosed and generated manager streams re-emit exactly, with all 46
schemas reached in both directions. The 36 linked Config/CMgr/Resolved checks
and six mate-stream checks also pass. A guarded four-document nested replay
retains zero runtime input reads, 36 stream comparisons and exactly the same
generated output. Process regressions cover the normal SDK metadata path,
Unicode authored names, shared-codec admission, malformed rejection and
compatibility diagnostics. Static checks and source fingerprints are recorded
in the receipt.

An authored extra-root syntax case also passes the separate typed research
round trip while SDK admission remains false in both directions. No native
validity is claimed for this discovery case.

This does not admit the whole Config-to-Resolved-to-Mates graph or register a
production writer. Semantic construction, native application measurements and
held-out qualification retain their separate requirements.

[Format and ownership rules](../../../../../re/solidworks/records/CmgrBodyGrammar2026.md)
· [Source and process receipt](../../../../../re/solidworks/measurements/2026/SdkCmgrGraph01.json)
· [Complete-graph boundary](../../../../Gotchas/Conversion/Solidworks/Archive/Configuration/ManagerGrammarDoesNotAdmitWholeGraphs.md)

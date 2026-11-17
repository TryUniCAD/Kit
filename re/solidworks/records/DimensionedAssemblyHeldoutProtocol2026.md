# Dimensioned assembly held-out protocol

This comparison covers the three- and four-occurrence assemblies
`A15HeldoutSyncedThree` and `A16HeldoutSyncedFour`. They share the
independently authored L1 rectangular child and one active configuration.
The [source lock](../v2026/heldout/AssemblySyncSourceLock.json) has SHA-256
`50de39dc21405cd346566f64244b62d457857758f339a95be4baf3466dfc1f80`.
Its authored specification has SHA-256
`b4d22e559b61ec1c1bae56c9c11fb97db05c040f5b01a94f129595e65e1cc922`.
The independently recorded native archives and outcomes remain sealed
through generation.

## Frozen generation

1. Use writer commit `23e01579fb0ad607417ddfc84e4fbb7b0c55b1be`, tree
   `1d6a9ee722f57e061725b43671498bf6fa3968e2`. Its six single- and
   repeated-occurrence discovery pairs passed all three driving edits with
   native source tree, configuration, transform and geometry parity.
   [Discovery measurement](../measurements/2026/GeneratedDimensionedAssembliesNative04.json).
2. Reproduce all six disclosed pairs at their originally encoded locations
   with [the prediction tool](../../tooling/sw2026/PrepareDimensionedAssemblyPredictions.py).
   Require every parent, child and request digest to match. Freeze the
   prediction tool, the [source binder](../../tooling/sw2026/BindDimensionedAssemblySources.py),
   the [native observer](../../tooling/sw2026/InspectDimensionedAssembly.py)
   and its dependencies, the source lock, exact output location and pinned
   SOLIDWORKS 2026 executable before consuming held-out authored parameters.
3. Run the prediction tool with only the authored specification and pinned
   writer source. Derive placement matrices from each authored axis, angle
   and translation. Use the independent L1 sketch, its recorded width and
   height text anchors, the forward blind depth and the canonical English
   system roles. The source of these model inputs is the authored ladder
   manifest. Emit the generated file, request and archive receipt hashes
   before opening the locked native archives or outcome records. The
   construction processes require zero runtime input reads.
4. Bind the independently frozen native references only after checking every
   prediction digest. Check both original native observation hashes and the
   parent and child file hashes against the source lock. Compare the ordered
   tree from the locked fresh rebuild. Stage both independent sources and
   matching generated artifacts in the declared private guest path.

## Native acceptance

Run the committed observer through the Windows 11 VM with the pinned
`SldWorks.Application.34` oracle. Exercise open, explicit rebuild, an
independent edit, synchronized child and parent save, and fresh reopen for
each of the three edits in both cases. Drive width to 50 mm, height to 25 mm,
and depth to 12.5 mm in separate copies. Require all phases, 26 distinct
process creation identities, both healthy controls and original file
immutability.

For each stage compare exact recursive parent and child trees, component name,
configuration, fixed and suppression state, all 16 transform entries and all
three named dimension values. Compare solid counts, volume, area and centroid
against the independent analytic prism targets and the paired native source.
For width and height, compare the two in-plane centroid coordinates against
the edited native source. The default assembly mass API uses a different
effective density from the isolated child. Compare assembly mass directly
with the matching native source mass. Keep zero open and rebuild diagnostics,
zero save warnings and an exact saved-child update stamp at fresh reopen.
[Discovery protocol and tolerances](DimensionedAssemblyDiscovery2026.md).

Publish the measured result for this ordinary placement profile and exact
generator revision. Production corpus conversion requires the separate
public writer and corpus acceptance.

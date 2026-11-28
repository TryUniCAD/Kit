# Final destination owns native self identity

An adapter's path argument can be a temporary transaction target. The normal SDK
`WritePathStaged` creates a staging directory and supplies the requested final
path separately in the existing `WriteOptions.values["final_destination"]`.
Using the temporary target as a generated SOLIDWORKS self-file reference would
persist an identity that disappears when staging completes.

The internal plain-part preparation bridge encodes the explicit final identity
and checks the staged/final filename. It does not resolve paths, inspect an old
model, reopen a donor, write a destination or infer a host-to-Windows drive map.
Binary preparation also needs an explicit final identity. Unnamed streams and
unmapped host paths remain outside the current fresh self-file profile.

These are current preparation rules. A standalone part that opens after
relocation does not by itself establish that an absent old self path, external
assembly reference or drawing reference can be ignored. Measure those cases
separately before broadening path admission. The public writer remains disabled.

The [bridge record](../../../../../../re/solidworks/records/SdkPlainPartAdapterBridge2026.md)
records the source contract, process proof and acceptance boundary.

The later narrow [standalone host policy](../../../../../../re/solidworks/records/SdkStandaloneHostPath2026.md)
can keep an explicitly authored neutral self locator for an absolute POSIX final
destination. The actual final basename still governs selection and must match the
neutral model. This exception claims no drive mapping and cannot supply linked
child-reference identity. The original Windows bridge proof remains bound to its
original snapshot.

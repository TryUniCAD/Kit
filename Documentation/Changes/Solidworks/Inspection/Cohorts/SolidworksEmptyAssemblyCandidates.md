# Generate reduced empty assembly candidates for native inspection

The research builder combines the empty assembly model, initial configuration,
resolved features, mate list and document definition with generated headers,
version history and biography. It uses the same rooted metadata serializer
as the part builder. The process gate reopens the generated container,
re-emits all four metadata streams and checks the configuration and resolved
map handoff while denying runtime file access.

The remote gate retains two generated `.SLDASM` candidates and their manifests
for the [native inspection](../../../../../re/tooling/sw2026/InspectEmptyAssemblyCandidates.py).
The inspector verifies the exact artifact and oracle hashes, brackets the
candidates with the native empty assembly and healthy solid-part controls,
and records open, rebuild, save and fresh-reopen behavior separately.

This reduced container omits the keyword index and unclassified optional data.
Whether these omissions are safe for an empty assembly is an open measurement.
Remote process and native evidence for these candidates are pending. This work
does not establish held-out acceptance or change public writer support.

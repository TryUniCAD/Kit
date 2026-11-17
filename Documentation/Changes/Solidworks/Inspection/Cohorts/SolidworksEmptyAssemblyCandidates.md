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

The reduced container omits the keyword index and 31 other streams present
in the native discovery control. The
[native measurement](../../../../../re/solidworks/measurements/2026/EmptyAssemblyNative01.json)
shows both generated files match the control's ordered 22-node tree,
single active configuration and zero bodies through open, rebuild, native
save and fresh reopen. All 10 candidate observations match and all four
controls pass across eight distinct launches. That omission result applies
to this empty assembly profile.

The [native-format job](https://github.com/TryUniCAD/Kit/actions/runs/44008628902/job/133789957496)
passed all 209 format checks on `7a79e796e` and published the two candidates.
That revision separately failed the Python name-length policy for an artifact
helper. The rename leaves construction unchanged. This work does not establish
held-out acceptance, populated assembly support or public writer support.

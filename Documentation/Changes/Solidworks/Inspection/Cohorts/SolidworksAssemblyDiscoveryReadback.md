# Read the empty and repeated-component assembly discovery archives

Three native discovery saves from the
[second source attempt](../../../../../re/solidworks/measurements/2026/AssemblySourceAttempt02.json)
are available for archive correlation. The selected files contain zero, one
and two ordinary occurrences of the same component. The source attempt remains
ineligible; both populated discovery files returned warning `32` on reopen.
The held-out files were not used.

The [fixture manifest](../../../../../re/solidworks/v2026/corpus/assembly-discovery/Manifest.json)
binds the three prepared files to their native hashes and warning values. The
preparer retained 127 streams, recorded 45 same-width metadata redactions and
exported three visually inspected previews. No archive schema ran during
preparation, and prepared containers were not reparsed on the host.

The remote [assembly reader](../../../../../re/tooling/sw2026/serial/AssemblySources.py)
compares seven complete archive streams per file and reports the typed model
and header values, graph identities, class counts and reference update stamps.
The reference projection checks both the configuration and its linked resolved
map and distinguishes separate reference objects with identical content. It
records the actual schema status for each stream. The [first remote receipt](../../../../../re/solidworks/measurements/2026/AssemblyDiscoveryProcesses6fc.json)
passes all 21 stream comparisons and finds the expected zero, one and two
ordinary references. The populated configurations retain external reference
markers and the original native warning. The additional stamp projection
still needs its remote result. Discovery adds no writer outputs or acceptance.

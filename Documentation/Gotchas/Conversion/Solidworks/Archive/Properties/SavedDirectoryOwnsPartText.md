# The saved directory owns configuration property identity

The numeric suffix in `docProps/Config-N-Properties.xml` identifies the
native configuration. In the typed saved directory, the configuration
header stores that ID in `f30`. Its `f08` field is the active flag.
The keyword index and the physical configuration streams are separate
records.

Verify the concrete saved directory row, its active flag and name and its
physical part streams before attaching text to a neutral configuration.
Read the live value from its configuration XML. After a native edit and
save, the separate configuration property cache can still contain the
previous text.
[Disclosed verification](../../../../../../re/solidworks/records/LiteralPartTextReaderSlice2026.md)

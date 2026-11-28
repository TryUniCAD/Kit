# The saved directory owns configuration property identity

The numeric suffix in `docProps/Config-N-Properties.xml` identifies the
native configuration. In the typed saved directory, the configuration
header stores that ID in `f30`. Its `f08` field is the active flag.
The keyword index and the physical configuration streams are separate
records.

The concrete saved directory row supplies the active flag and name. A
physical `Config-0` stream can be nonempty and still end partway through
the model. Physical admission requires the ordinary typed configuration
codec and the same decoded ModelHeader objects used by the configuration.
The linked reader invokes the complete ordinary configuration read
before projecting any literal bags. A same-width reference to a real
header object still fails when the field belongs to the enclosing part.

Read the live value from its configuration XML. After a native edit and
save, the separate configuration property cache can still contain the
previous text.
[Disclosed verification](../../../../../../re/solidworks/records/LiteralPartTextReaderSlice2026.md)

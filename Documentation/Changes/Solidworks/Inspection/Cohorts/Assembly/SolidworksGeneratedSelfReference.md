# Generate the ordinary assembly self reference

The empty SOLIDWORKS 2026 research builder accepts an optional `output`
mapping with `path_name` and `saved_at`. It constructs the ordinary
file record from the generated assembly model, its active configuration,
its creation time and the provided save-event Unix timestamp. The model
name and output filename can be different.

Both headers serialize the record. The configuration archive registers
the model header's actual object in its first direct slot. The writer
uses the supplied path and timestamp as data. The guarded process checks
the generated header fields, slot identity, archive round trips and
runtime file-read boundary. Remote process and vendor results are pending.

This research entry applies to an empty assembly. The
[2026 construction evidence](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#ordinary-self-reference-construction)
records the native factory, connection, timestamp and archive rules.

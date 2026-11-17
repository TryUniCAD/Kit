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
runtime file-read boundary. The [native format job](https://github.com/TryUniCAD/Kit/actions/runs/44018181604/job/133821039190)
produced a 6,268-byte candidate with nine generated streams and no runtime
file reads. Its two headers agreed and the file record occupied slot 3.

The vendor probe accepts one or more distinct frozen candidate files and
requires a separate reopen process and the same four control launches
around each batch.

The [SOLIDWORKS 2026 SP05.2 measurement](../../../../../../re/solidworks/measurements/2026/AssemblySelfReferenceNative01.json)
records a clean open, rebuild, save to a separate file, and clean reopen.
All five observations matched the empty control's 22-node tree, active
configuration, body count and rebuild state. Four controls passed across
six fresh processes. The license process IDs observed before and after
were identical.

This research entry applies to an empty assembly. The
[2026 construction evidence](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#ordinary-self-reference-construction)
records the native factory, connection, timestamp and archive rules.

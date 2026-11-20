# Learning both extrusion end bindings

After recovering a saved edit, the decoder varies other declared extrusion ends in a private copy of the reconstructed graph. For each candidate it changes the driving parameter and feature property together, emits the expected native objects, and requires exactly one mapping that changes only the chosen end. The temporary values are never written to the input or the reported candidate.

Before exporting Reader.patch, the decoder freezes the discovered bindings and runs the generated Python reader in separate processes on hash-pinned native saves other than the input. Each emitted binding must recover an edit on another file and pass the native graph and shape checks. Input-reader-patch.json distinguishes bindings recovered from the actual input edit and lists the files used to corroborate the reader. The result covers the particular end fields and graph shape exercised.

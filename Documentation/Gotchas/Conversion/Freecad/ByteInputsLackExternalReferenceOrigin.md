# FreeCAD byte inputs lack an external reference origin

The FreeCAD reader uses the actual source file's parent to resolve linked component documents through its guarded path resolver. An otherwise identical input supplied as bytes has no usable file origin for that lookup.

A comparison of 162 available FCStd identities produced the same strict read, timeline, sketch relation and assembly counts in both modes. One linked document resolved from the file path and reported `freecad.unresolved_external_documents` from bytes. Strict read success by itself does not establish that external links resolved. [Read census](../../../../re/solidworks/measurements/2026/NeutralCorpusRead01.json)

Read assemblies from their actual source paths with the linked files available when checking external references. Verify the returned component documents and diagnostics before passing the neutral assembly graph to a writer.

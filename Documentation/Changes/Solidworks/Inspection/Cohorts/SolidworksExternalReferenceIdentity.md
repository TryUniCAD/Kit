# Inspect the ordinary assembly external file directory

The synchronized assembly readback now records the two header directories,
including named file entries, configuration selectors, registration counts
and direct-reference slots. It also reports how each occurrence stores its
external binding. The report omits absolute paths and reads only the three
disclosed assembly fixtures. Both populated held-outs remain sealed.

The [native lookup trace](../../../../../re/solidworks/records/AssemblyConstruction2026.md#ordinary-external-file-identity-in-the-header)
identifies the equality rule for normal file entries: document kind,
creation time and case-insensitive filename stem. A distinct folder path
does not separate entries in this lookup.

The existing remote readback gate will exercise the new projection.
It does not build a populated assembly or establish writer acceptance.

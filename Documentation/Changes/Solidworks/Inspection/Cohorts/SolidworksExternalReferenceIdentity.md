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

The [remote readback](../../../../../re/solidworks/measurements/2026/AssemblyExternalDirectoryEA67.json)
passed 35 complete stream comparisons. The two occurrences in the repeated
case share one header entry and archive slot, while the entry's active-user
count reflects both occurrences. The child directory timestamps also differ
from the occurrence's child-header update timestamp. This evidence does not
build a populated assembly or establish populated writer acceptance.

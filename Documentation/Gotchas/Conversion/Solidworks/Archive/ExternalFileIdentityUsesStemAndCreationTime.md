# The ordinary external-file lookup does not compare folder paths

Two referenced parts can have distinct paths but the same identity in the
header's ordinary external-object lookup. The native equality operator
compares the document kind, creation timestamp and case-insensitive filename
stem. It does not compare the full path. Its graphics-reference branch has
different rules.

Keep the full path in the generated file definition. Treat distinct authored
files matching the ordinary equality key as a collision to resolve or reject,
not as interchangeable references. The
[native lookup trace](../../../../../re/solidworks/records/AssemblyConstruction2026.md#ordinary-external-file-identity-in-the-header)
binds the rule to the pinned 2026 binary. Populated collision behavior has not
been measured.

# Read a cold SOLIDWORKS rotated three-mate assembly

Strict SDK reads recover the ordered parallel, distance and coincident mates
of the qualified version-19000 cold assembly. Both occurrences resolve to
their actual shared part. Kit binds six datum picks, the fixed occurrence
and the live D1 distance. The full reader derives the rectangular child
solid from its typed sketch and boss. `include_brep=False` retains the same
mates and parameters.

Set `resolve_components=False` to keep the occurrence inventory and raw
mate stream while deferring linked mate semantics. The rotated three-mate
profile is read-only. The complete-suite case builds both files from an
independent neutral recipe in a separate process.
[Verification record](../../../../../re/solidworks/records/ColdRotatedMateAggregate2026.md)
[Complete-suite case](../../../../../tests/Convert/Solidworks/PlanarWriting/ColdRotatedMateTests.py)

# Saved selection strings do not define actual mate endpoints

The legacy mate reader can return no entities when a generated assembly
omits saved selection strings. This does not establish that its resolved
mate references are missing. The separate MatesList stream can still contain
both complete plane wrappers and their actual inherited occurrence chains.

In the six disclosed 2026 pairs, the three native saves have two legacy
string entities, while the three generated counterparts have none. All six
have two resolved plane references with valid child identities and datums.
The old public route rejected the generated mates at document validation.

Use the complete typed linked graph for the qualified ordinary profile.
Require the actual resolved map, parent occurrence ownership, synchronized
child file/configuration/stamp, selected datum and consistent plane geometry.
Do not replace missing entities with guessed names or bypass validation.
If those checks cannot complete and the legacy entities are empty, report
the exact typed rejection cause. Other profiles keep their existing reader.
[Public reader and frozen comparison](../../../../../../re/solidworks/records/PublicTypedPlanarMates2026.md)
[Separate-stream ownership](MateGroupChildrenLoadFromSeparateStream.md)

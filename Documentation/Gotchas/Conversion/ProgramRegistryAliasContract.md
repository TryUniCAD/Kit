# Program registry alias contracts

## Expectation

A generic recovery tool can read every facade through inline owner and operation declarations, or resolve a missing table to a registry attribute with a `K` prefix.

## Actual behavior

Existing families expose part of their contract through `Registry.py`. A registry's current attribute name alone does not establish whether the source needs one resolved stream or multiple stream mappings. Selecting `KStreamPrograms` merely because it exists can rebuild assembly metadata as a single `Contents/CMgr` program and discard the other stream mappings.

Some source facades also preserve legacy aliases such as `StreamPrograms` alongside `KStreamPrograms`. Loading and regenerating those bindings without respecting the declared public aliases breaks imports before a verifier can inspect the resulting graph.

## Workaround

Do not rebuild unrelated catalogs when introducing one independently recovered family. Use `re/tooling/ProgramDecomposition/AddProgram.py`, which reads one `resolved/polyline/<family>/Program.py` and renders only its family registry and methods. Its `--program-root` argument is required so an invocation cannot silently select the production adapter tree.

Reuse an owner module only when all required owner key/value pairs are a subset of the existing catalog. Extra existing owner sites must remain untouched. Adding a missing module is fine; silently merging incompatible values is not.

The additive path verifies the full old and new registry without altering established aliases. Restoring the intended baseline after exploratory regeneration gives the previous verified counts again; do not interpret that recovery as proof that the full rebuild is safe.

See [the additive generator](../../re/tooling/ProgramDecomposition/AddProgram.py) and [the triangle change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md).

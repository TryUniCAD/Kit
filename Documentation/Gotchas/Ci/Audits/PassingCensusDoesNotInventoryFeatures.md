# A passing reader census does not inventory recovered features

Expected: a green corpus check identifies which CAD feature sets were interpreted.
Actual: the existing census checks record decode modes and receipt integrity, and their temporary decoded documents are deleted.
A partial decode or native-only feature record can satisfy that observation without proving a complete parametric feature set.

Use a manual audit with `feature_session=true` and inspect the preserved `CadFeatureSession` artifact.
Its per-file feature inventory keeps interpreted definition types, native-only records, missing definitions, and unresolved evidence visible.
Counts and successful serialization still do not establish losslessness or native acceptance.

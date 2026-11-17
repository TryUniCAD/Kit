# Archive class and object map rows have different widths

The compatibility map uses `(kind, name, schema)` for class entries and
`(kind, node)` for object entries. Destructuring every entry into two values
fails on the first class, before any linked reference evidence can be read.

Read the kind first and take its payload only after checking the kind. When
walking a configuration and its seeded resolved map, deduplicate inherited
objects by identity; repeated components can still have separate reference
objects. The [failed remote projection](https://github.com/TryUniCAD/Kit/actions/runs/43996766048/job/133750621506)
captured the width error on all three assembly discovery files.

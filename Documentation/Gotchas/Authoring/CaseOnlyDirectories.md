# Case-only directories

`Docs/` and `docs/` might appear distinct. A case-insensitive filesystem treats them as the same directory. Use `Documentation/` for maintained pages. Preserve the separate generated `docs/` path.

A checkout that integrates a directory-casing migration can retain its old physical spelling even when Git's tracked paths already use the new spelling. On macOS, a newly created file can then appear as `tests/convert/solidworks/...` while the canonical tracked tree is `tests/Convert/Solidworks/...`. In this state an explicit add through the canonical spelling returned success without staging the new process test.

Inspect both the physical directory names and `git diff --cached --name-status` before committing. For an unambiguous case-only mismatch, rename the physical directory through an unused temporary sibling, then to its canonical spelling. Preserve every file and the existing tracked index. Add the new path again and verify that its canonical name is staged. Do not create duplicate case-folded directories or rewrite unrelated tracked content.

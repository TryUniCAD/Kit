# Retired file notices can leave stale restrictions

## Expected behavior

Removing per-file license boilerplate leaves repository licensing documented by the governing license and separate attribution records.

## Observed behavior

Some Fusion research files retained restriction paragraphs after their SPDX labels were removed.
The verified decode evidence publication copied the same obsolete restrictions into new pages.
The repository [license](../../../LICENSE) specifies MIT terms.
The review identified the [incorrect evidence header](https://github.com/TryUniCAD/Kit/pull/120#discussion_r4576216450).

## Workaround

Read the governing license before writing licensing statements.
Remove the complete obsolete restriction block, and preserve attribution in the relevant standalone record or guide.
Search tracked text for stale license names and restriction paragraphs before publication.
Preserve independently licensed third-party materials and their notices.

See the [contribution guide](../../Reference/Overview/Contributing.md#licensing) and [correction entry](../../Changes/LicensingAccuracy.md).

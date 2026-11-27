# Accented fixture paths can appear untracked on macOS

A checkout should associate each fixture with its tracked path.
On macOS, Git can report an accented filename as untracked when its Unicode spelling differs from the stored path.

During PR #230, the V8 engine example contained 63 tracked paths and 16 reported untracked paths.
The inspected untracked names had tracked equivalents after NFC normalization.
For example, the stored `ADMISIÓN` spelling and reported `ADMISIÓN` spelling encode the accent differently.
These paths were present before the CI task. Filename equivalence does not establish file-content equivalence.

Stage explicit task-owned paths when unrelated fixture names appear in status.
Leave those fixture files unchanged during unrelated work.
A separate correction must verify content and preserve fixture references before changing their tracked spelling.

See [PR #230](https://github.com/TryUniCAD/Kit/pull/230).

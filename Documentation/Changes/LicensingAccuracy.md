# Licensing documentation accuracy

Kit uses the [MIT License](../../LICENSE).
The verified decode evidence pages and Fusion research files no longer carry obsolete license restrictions.
The evidence guide and Fusion attribution record retain their copyright attribution.

[Agent guidance](../../AGENTS.md#licensing-accuracy) now requires correct licensing for every added or changed artifact.
The [contribution guide](../Reference/Overview/Contributing.md#licensing) requires verification against governing license files and applicable third-party notices.
Third-party materials retain their own terms.
This correction does not relicense third-party material or restore retired per-file notices.

## Verification

Source inspection compared the corrected statements with the repository license and existing attribution records.
A case-insensitive search of tracked text found no remaining references to the obsolete restriction.
The separate third-party codec license reference remains unchanged.
Prettier 3.6.2 accepted all changed maintained Markdown files.
`git diff --check` passed.
No local tests ran; PR CI and configured review supply separate revision-specific evidence.
Rendered documentation and complete language-standard conformance remain unverified.

See [the stale-notice gotcha](../Gotchas/Licensing/RetiredFileNotices.md).

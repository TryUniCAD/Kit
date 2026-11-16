# Project naming cleanup

Repository text now uses Kit branding and current `TryUniCAD/Kit` links.
Support and security pages follow the repository contribution and private-reporting policies.
Copyright notices retain the named individual authors.

The JSON adapter advertises `application/vnd.kit+json`.
Consumers that compare the previous media-type string must update their configuration.
The JSON format identifier and serialized model schema are unchanged.
FreeCAD document creator and comment properties now identify Kit.

Obsolete security and rationale-policy directory exclusions are removed.
The remaining CI gates and exclusions are unchanged.
External FreeCAD example lookup now uses the sibling `FreeCAD/` checkout.

Historical research paths omit the retired parent directory name.
These normalized paths identify research locations, not verified current filesystem locations.
Measurement values and model digests are unchanged.
Readable standards normalize project naming and external fork paths.
The pinned historical source, original hashes, and complete inventory checks remain intact.
See the [normalization gotcha](../../Gotchas/Policy/HistoricalNamingNormalization.md).

## Verification

A case-insensitive tracked-content search found no remaining references to the retired name.
A tracked-path search found no filenames containing that name.
Prettier 3.6.2 accepted the changed maintained Markdown, JavaScript, and YAML files.
Black 25.1.0 accepted the five changed Python files.
`git diff --check` passed.
No local tests ran.
Remote CI and automated review must be checked on the accepted PR head.
CAD application acceptance, rendered documentation, and complete language-standard conformance are unverified.

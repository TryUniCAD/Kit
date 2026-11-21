# Folder feature construction uses FILETIME

## Expectation

A folder whose public constructor accepts an owner uses the same feature-base
initialization as owner-taking geometric features.

## Observed behavior

The 2026 `moFolder_c` constructor at `sldmodu` `0x4beae110` first calls the
default feature constructor `0x4bb38710`, then assigns the owner.
The default constructor obtains FILETIME for `f2a0/f2a4`.
The owner-taking feature constructor `0x4bb38350` instead initializes those
fields to zero.
The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
lists the derived-folder constructors and their stored fields.

## Workaround

Keep the native constructor variants distinct.
Build folder creation-time words from explicit creation metadata and the
FILETIME epoch conversion; do not reuse a geometric feature's zero timestamps
or copy timestamp words from a saved folder.

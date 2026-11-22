# Project attribution and README corrections

## Behavior

Kit identifies Odin Glynn-Martin, Stephen Harcourt, and James Harcourt as core contributors and copyright holders.
The README, MIT license, owned source notices, and retained policy fixtures use those names.
Third-party licenses remain intact.

Obsolete organisation references are removed from tracked text.
Support and security links point to `TryUniCAD/Kit`.
Unused legacy workspace exclusions are removed from security and rationale checks.
The JSON adapter advertises `application/vnd.unicad.kit+json`.
FreeCAD output identifies its authoring application as `Kit`.

## Usage

Open the Kit repository directory before running `uv tool install .`.
Use a real `model.f3d` file and an unused output path for the README command examples.
Square brackets are not part of the input filename.

See [the README](../../../README.md), [contribution guidance](../../Reference/Overview/Contributing.md),
and [JSON adapter metadata](../../Reference/Adapters/Json.md).

## Limits

The JSON media-type label changes; the interchange document schema does not.
Consumers that inspect the label must use the current value.
Historical research path labels use the current organisation spelling.
Those normalized labels do not assert the original host directory names.
Recorded measurements and CAD fixture bytes are unchanged.

Readable historical standards have explicit byte edits in their provenance manifest.
CI still verifies every original blob, hash, size, and inventory entry before applying those edits.
The source commit remains pinned.
See [the preservation gotcha](../../Gotchas/Ci/Policy/StandardsReadableEdits.md).

## Verification

The complete tracked-text search found no obsolete organisation references after editing.
`git diff --check` passed before publication.
Local tests and CAD procedures were not run.
Remote CI and current-head review provide the remaining verification evidence on the PR.

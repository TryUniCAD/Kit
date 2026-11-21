# Native local-import keyword index

Three disclosed current-format imports reproduce the source's 25 keyword roles, captions and tags on the generated model's own persistent IDs. At the same locator, opting in changes only `swXmlContents/KeyWords`. The three frozen legacy files still reproduce byte-for-byte. [Host stream receipt](../measurements/2026/ImportedNativeKeywordIndex01.json)

## Typed index

The index enumerates the resolved roots, the actual environment's counted light list, the cabinet's reciprocal notes pair and the direct part manager when present. Seventeen rows reuse the existing assembly role vocabulary. The part uses `Plane` for the three reference planes, adds `Surface Bodies`, `Solid Bodies`, `SOLIDWORKS Materials` and `Imported`, and binds the shared `Exploded Views` label to its own concrete manager. The common origin is `Sketch` with type `Origin`. The manager row has an explicit empty name. No item receives a fixed source ID or a captured index position. [Shared owner and role rules](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/ReadImpKeyNodes.py) · [Part manager evidence](PartExplodedViewConstruction2026.md)

The configuration comes first. The following rows sort by XML tag and the decimal text of their actual ID. The frame uses the existing unsigned epoch root ID, UTF-8 declaration, leading `0x86`, CRLF, and compact empty tags. Native framing follows the explicit index input. The no-manager control produces 24 rows through the same logic.

## Index-specific metadata

`ImportKeyInput` takes a title, a dedicated unsigned epoch and the selected configuration's display material label. The disclosed projection obtains the title and epoch from the same source index and checks the title against its typed source model. It checks the configuration material label against the actual unassigned material folder and the neutral configuration's retained native property. The three sources contain no material assignment. These index values do not alter the output filename, binary model and self names, or Header chronology. [Typed input](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/ImportKeyInput.py)

| Source | Index title | Index epoch | ModelHeader update epoch | Configuration material |
| --- | --- | ---: | ---: | --- |
| Disclosed | Part1 | 1795127796 | 1795127810 | Material &lt;not specified&gt; |
| Other shape | Part1 | 1795130644 | 1795130664 | Material &lt;not specified&gt; |
| Renamed feature | Part1 | 1795130833 | 1795130857 | Material &lt;not specified&gt; |

## Scoped read admission

The local fallback validates the original XML index against the actual linked graph and manager-selected configuration before it can use the normalized import feature. Canonical serialization of those owners must reproduce the raw index. This binds all IDs, captions, tags, roles, configuration material, lexical order and framing. The separate root title and epoch keep their own encoding. The ordinary payload decoder retains precedence, and the prior class-name indexes still use the legacy fallback. [Raw index binding](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/ReadLocalKeys.py) · [Fallback selection](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/FindLocalOwner.py)

The prior name repair maps an unused source import ID 26 to the generated import ID 18 when the caption matches. The new raw check refuses that stale index even after the legacy parser has repaired the in-memory feature. Other refusals cover omissions, duplicates, a manufactured manager name, cross-bound light and configuration labels, and removal of the actual manager while its XML row remains.

## Reproduction

The [observer](../../tooling/sw2026/imported_body_source/VerifyNativeImportKeys.py) loads the hash-bound disclosed sources and previous output references from the exploded-view packet. It converts each source to typed geometry, scene, notes, property and index values before construction. The guarded writer receives only those values. Three exact earlier outputs, three deterministic indexed outputs, an index without a manager, two unchanged generic keyword dialects and eighteen malformed read refusals are recorded. Each indexed output yields one strict SDK local solid. The three indexed outputs have Config and Resolved map counts 103 and 171, with import ID 18 at map index 168 and manager ID 25 at map index 102.

```sh
uv run --offline --no-project --python 3.13 python -B re/tooling/sw2026/imported_body_source/VerifyNativeImportKeys.py "$DISCLOSED_PACKET" | diff -u re/solidworks/measurements/2026/ImportedNativeKeywordIndex01.json -
```

This receipt covers host stream parity and strict SDK geometry readback.

## Native save contrast

All three generated files open, rebuild, save and reopen with zero open
errors or warnings. They retain the original ordered 24-row COM feature
trees, the authored lights, notes, empty exploded-view managers and
property owners. Both controls pass across eleven fresh processes.

The native saves retain all 25 indexed role, name and tag rows and the
allocated import ID. SOLIDWORKS changes the keyword root title to the
actual generated part name and uses its modeled save timestamp. It omits
the configuration's optional unassigned material attribute while the
typed material folder remains unassigned. The first strict read guard
requires the attribute and refuses all three saved indexes. Exact
reconstruction of the same typed owners with the attribute omitted
matches all three saved streams. [Native save contrast](../measurements/2026/ImportedNativeKeywordSaveContrast01.json)

The corrected reader accepts that exact omission only for the proven
unassigned material folder. All three saved archives now bind the same
import ID and read a single strict B-rep body. The original generated
files with the supplied material label and the earlier legacy files
regenerate byte-for-byte. A model-only omission changes only the
keyword stream, and contradictory text or nonempty physical material
ownership fails closed. [Saved-copy replay](../measurements/2026/ImportedNativeKeywordSavedReplay01.json)

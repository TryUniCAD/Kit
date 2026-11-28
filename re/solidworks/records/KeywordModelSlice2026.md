# SOLIDWORKS 2026 typed KeyWords model

The [expanded typed corpus](KeywordTypedCorpus2026.md) records saved radius,
diameter, cut order, empty sheet-metal and assembly occurrence forms.

| Delivery item | Scope |
| --- | --- |
| Task | `B03-SW2026-KEYWORDS-MODEL` |
| Owner | PR #121 takeover team |
| Delivery | Independent main-target component within PR #121's B03 programme |
| Prerequisite | [KeyWords framing](https://github.com/TryUniCAD/Kit/pull/181), based on [the accepted main revision](https://github.com/TryUniCAD/Kit/commit/57f519c9851ef8f4aacd7472f86f5ecaf7bd163e) |
| Exit | Guarded fresh-process emission and XML readback, independent byte assertions, refusal checks, current-revision review and CI |

## Source boundary

The eight extracted source files originally matched
[the aggregate](https://github.com/TryUniCAD/Kit/commit/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f)
and [the local-import native trial generator](https://github.com/TryUniCAD/Kit/commit/67b2fa8b2aee19bade296f764bf7267afcbc72ca).
The original source manifest SHA-256 is
`b73bb83021ead2ce7c35df3cad172814434831844c31c671e2ac1d30dacd0535`.
It covers `Metadata/{KeywordConfig,KeywordDim,KeywordFeature,MakeKeyDimMut,MakeKeyFeatMut,MakeKeywords}.py`
and `Styles/{ReadStyleNum,ReadStyleText}.py` under
`src/convert/adapters/solidworks/Archive/Construction/`.
The manifest hashes the sorted repository-relative paths, each followed
by a NUL, its lowercase SHA-256 and a newline.

The eight files use the standard library and the existing
[`FrameKeywords`](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/FrameKeywords.py).
The scoped review tightens `MakeKeyFeatMut` to require one degree-valued
`D1` on the ordinary revolve. `MakeKeywords` preserves that profile
and accepts the native dimensioned, dissectable linear sketch with explicit
compact framing. The other six files remain unchanged. The current
eight-file manifest is `cd618ade027ec2e4c13d801b4072d51f7fefd691c053abed14bfd196a52fea67`. Including the eleven
accepted framing and XML boundary files gives `cba703c96fe447cc4033fdef8c012208ddb9d9e9a9a001e87a331b41cbfc7d67`.
The first main-based nineteen-file manifest was
`69d1335a739df92c85071c4fe6c64a532561ecc7ea9b307e5f00d894e99db7c0`.
The historical nine-file manifest before the framing repair was
`aeefcf90569fa878348122c972135d67b6001ebde636d53a7edee6094c2088f9`.
[Framing provenance](KeywordFrameSlice2026.md)

## Field ownership

The model emits the internal `swXmlContents/KeyWords` wire stream.
Its caller supplies already projected rows from a chosen graph and profile.
Neutral document and native graph resolution belong to the caller.

| Wire field | Status in the slice | Source and rule |
| --- | --- | --- |
| Root ID and name | Input | The exact `Keywords` root stores an unsigned 32-bit Unix epoch and the model title. The part callers supply the authored title and actual header modification event. |
| Configuration ID, name, type and material | Input and declared vocabulary | The graph projection uses the manager configuration node's `f08` and name. The wire row writes `ConfigurationManager` and the supplied material text. The measured generated profiles supply empty material text. |
| Feature ID, name, tag and type | Input and profile vocabulary | Use the allocated feature node's `f08`, actual name and the declared role. The typed rows accept `Feature`, `Sketch` and `Extrusion`. Common system rows carry their actual class name. Measured kind tokens include `Imported` and `Revolve`. |
| Row and attribute order | Derived framing | Configuration rows precede feature rows. Each tuple retains its supplied order. Dimensions stay under their owning feature. Optional flags are lowercase booleans when present. |
| `DissectableChildren` | Bounded derived index | The emitter permits one positive decimal feature ID and checks its membership. The cut composer derives it from the actual selected profile node. The wire component assumes the caller has checked graph roles and relationships. |
| Linear dimension name and text | Input and numeric encoding | The sketch projection reads the actual parameter name and `f58` length in metres, then divides by the document length-unit scale. The emitter receives the result in presentation units. It emits no unit suffix for a linear value. |
| Omitted cut type and depth | Bounded profile vocabulary | An `Extrusion` without `Type` requires one child. A blind cut supplies the actual depth as `D1`. A through-all cut can omit depth when it has no distance owner. |
| Angle text, sketch type and empty tags | Bounded profile vocabulary | The revolve projection converts the authored angle from radians to degrees. The `Feature` of type `Revolve` has one degree-valued `D1`. A dissectable sketch can omit its type when it has dimensions or appears in the angular profile. The angular profile selects compact tags. The caller chooses compact tags for observed native linear profiles. The initial generated linear and local-import profiles use spaced tags. |

Configuration and feature IDs have independent uniqueness checks. The emitter
formats integers directly and floats with `.17g`. Duplicate dimension names
within one feature, nonfinite scalars and unclassified units fail explicitly.
The caller supplies XML 1.0 text and the text helper rejects NUL.
The caller owns unit conversion. The pinned length projections support
scales of `0.001`, `1` and `0.0254` metres per mm, m and in, respectively.
[Part graph projection](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Construction/Part/MakePartKeys.py)
[Sketch parameter projection](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Construction/SketchDimensions/MakeSketchKeys.py)

The native [framing audit](https://github.com/TryUniCAD/Kit/blob/889fb6dffcad5ed3b0a065e07c21a53979a17be7/re/solidworks/records/KeywordCorpusFraming2026.md)
observed compact empty tags across 88 sources, including linear parts.
Its six child references establish the single decimal form. Material
assignment authority, localized numeric text, multiple-child grammar,
drawing and assembly vocabularies, and arbitrary native index regeneration
remain outside this extraction.
[Native sketch type variation](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Metadata/KeywordSketchTypeDependsOnProfile.md)

## Disclosed profile evidence

The tracked [fixture receipt](../measurements/2026/LocalImportReadbackFixtures01.json)
binds the original neutral input hashes, both controls and native lifecycle
measurements using SOLIDWORKS `34.5.2.0604`. The fixture streams each carry one
configuration and 18 ordered features, including an `Imported` row. Both use
spaced tags and have zero dimension rows and child references.

| Tracked generated fixture | Whole file SHA-256 | KeyWords stream SHA-256 | Stream bytes |
| --- | --- | --- | ---: |
| [ConcaveOwned](../v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT) | `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33` | `067f823ee629cb6477d074d1177f65d5b8ca93843bb13c979b0a11ba02e55b28` | 1,306 |
| [RectangularBare](../v2026/corpus/local-import-readback/RectangularBare.SLDPRT) | `302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357` | `6b9d298647fccf2baa908f65d5cc86ad36e14a17b9bbea12554042f1bb27d425` | 1,309 |

The [native L1 boss](../v2026/corpus/ladder/L1_boss.SLDPRT), SHA-256
`55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6`,
has a compact 1,739-byte index with SHA-256
`507f9c7c1b6c4a70ea1ab7fe4c3e66b4cbab6f46168dc5e1338c5710499a69ef`.
Its sketch 26 carries two linear dimensions and no type. The same
index has an empty name on the exploded views row and a literal
unassigned material on its configuration. The new guarded queue
case projects the source rows as typed model values, emits the stream
in a separate process and compares its exact size and digest.
[Native linear queue case](../../../tests/Convert/Solidworks/KeywordModels/KeywordNativeLinearTests.py)

The [blind boss receipt](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/measurements/2026/SdkBlindPartNative01.json)
binds a generated 1,420-byte index with a live depth. The
[blind pocket proof](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/SdkBlindPocket2026.md)
ties its single child ID and depth to the actual cut and sketch owners. Both
use an earlier copy of `MakeKeyFeatMut` that required `D1` on a cut.

[Through-all generation](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ThroughAllColdConstruction2026.md)
extends that rule to a cut with no distance owner. Its `Extrusion` row keeps
the resolved profile ID and omits the dimension. The
[G01 native receipt](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/SdkThroughAllCutNative2026.md)
records the clean rebuild and fresh reopen of the exact generated part.

The [revolve construction report](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/SdkRevolveConstruction2026.md)
uses the exact eight source files at
[`80094b57`](https://github.com/TryUniCAD/Kit/commit/80094b57f8ea2e8d2312e613f8cd2875107a500e).
It binds guarded generated stream comparisons and the separate
[native lifecycle receipt](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/measurements/2026/SdkOrdinaryRevolveNative01.json)
for four exact-build disclosed parts. These construction results are
historical whole-file observations with their own producer revisions.

## Process boundary

The new [worker](../../tooling/sw2026/CheckKeywordModel.py) imports its code
and obtains its one standard-input payload before installing the audit guard.
The guard rejects runtime file opens, directory enumeration, subprocess
creation and native-library loads while encoding or parsing. The worker
publishes bytes on standard output after the guarded operation returns.

The [positional case](../../../tests/Convert/Solidworks/KeywordModels/KeywordPositionalTests.py)
authors unordered IDs across two independent namespaces, Unicode labels,
two sketch dimensions including a value whose decimal text needs 17 digits,
and distinct cuts with and without depth. The
[angular case](../../../tests/Convert/Solidworks/KeywordModels/KeywordAngularTests.py)
authors a consumed sketch and a `147.5°` driver. Each compares complete
independently specified wire bytes and uses a separate interpreter with
the existing XML parser to check the emitted rows. The
[refusal case](../../../tests/Convert/Solidworks/KeywordModels/KeywordRefusalTests.py)
checks seventeen invalid row or dimension forms and requires empty
output. Angular controls reject an absent dimension, unitless `D1`,
a degree-valued `D2`, a second dimension and a revolve with the
sketch tag despite a valid degree driver. Dimensioned type-less sketches
with an omitted or false dissection flag also refuse.

The process cases use authored metadata and no source CAD files. Scoped Black,
Ruff, Mypy, Pyright and steering checks passed for 13 Python files. The donor
scan found zero recorded payloads across 3,301 production files. Process
execution and exact-revision review await CI.
The component supplies stream evidence within
[the CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
Document conversion, application acceptance and feature authority have
separate exits.

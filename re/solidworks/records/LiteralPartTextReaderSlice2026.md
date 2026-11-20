# Main-target compatible part text projection

Task `B04-SW2026-PARTPROPS`. The main-target reader reuses the
version-19000 configuration directory and body codec from PR #178 on
base `76877b1c8b223f11ddf38c79dc10a2a878fc019e`. It uses the measured
literal XML grammar from aggregate revision
`8302c824a15830b837c72db75f79cabe5693d200`. The native controls and
independent text observations come from SOLIDWORKS 2026 SP05.2 build
`34.5.2.0604`.

| Scope | Wire owner | Qualified fields |
| --- | --- | --- |
| Summary | `docProps/core.xml` | Title, subject, creator, keywords and description |
| Document custom text | `docProps/custom.xml` | Ordinary text rows, matching evaluated text, separate PID/name dictionary |
| Configuration custom text | `docProps/Config-N-Properties.xml` | Ordinary text rows and optional equal evaluated text for one active configuration |
| Binary compatibility | `Contents/CusProps` | Absent or schema-one empty `moCusPropMgr_c` at map base 1 with `f0c=-1`, `f08=0`, `n20=0`, `f54=0` |

The native save routine writes the actual configuration ID and name to
`dmConfigHeader_c.f30` and `f10`. The reader requires one such row, active
`f08=1` and no parent `f34=-1`. It matches the neutral configuration ID
and name and requires nonempty physical configuration and resolved-feature
streams. The valid directory is a prerequisite for
configuration XML. The separate full configuration manager and its
embedded value cache are outside this reader's property path.

XML goes through the SDK's existing untrusted parser after strict UTF-8
decoding and rejection of NUL and other encoding declarations. Its
document-type guard runs before interpretation. The text projection
keeps explicit names and values and refuses unmeasured variants,
expressions, populated managers and conflicting owners. Scope admission
is atomic. Inspection keeps the same geometry and feature
semantics when optional properties are unavailable.

[Native property owner evidence](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/PartPropertySources2026.md)
· [Independent native text lifecycle](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/SdkPartTextProperties2026.md)
· [Configuration directory field evidence](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/ConfigurationManagerHeader2026.md)

## Reproduction

Run the focused verifier with the disclosed property packet root. The
three supported public documents compare all 23 recovered values to
independent native observations. The advanced rectangle retains a solid
and 26 feature rows while withholding all optional text. The four
public reads match their previous whole documents after removing only
the added property projection, its information diagnostic and the
derived semantic fingerprint. Recomputing that fingerprint matches the
previous read.

The two generated files retain the same public refusals for missing
Parasolid payloads and unresolved sketch support. Each of their property
graphs is checked separately using the exact source archive and its actual
typed directory link. Together they yield 15 literal values matching the
neutral author requests.

Twelve in-memory negative cases vary the saved directory, physical
configuration, or XML and withhold all optional text while preserving
the prior document. The six fresh host processes hash-check the exact
disclosed inputs, which stay outside the checkout.

```sh
python -B re/tooling/sw2026/VerifyLiteralPartText.py /path/to/disclosed-root
```

[Process tool](../../tooling/sw2026/VerifyLiteralPartText.py)
· [Revision-bound host receipt](../measurements/2026/LiteralPartTextReader01.json)

## Merge queue control

The Kit research team authored `CircularProperties.SLDPRT` as the radial
coupon control. The native author recorded the three summary values, three
file values and two configuration values independently through SOLIDWORKS
2026 SP05.2. The author record SHA-256 is
`2d3e7c0fdb5e32d482e5fde77b7b8359bbed07dda8e937856fb3979c49e3ee7c`.
The exact save preserves its native attribution and model data. It is
an input to the read regression.
[Native author and control receipt](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/measurements/2026/PartPropertySources01.json)
· [Fixture](../v2026/corpus/part-properties/CircularProperties.SLDPRT)

Before copying, the native format-4 directory verified 40 unique streams.
The stream inventory SHA-256 is
`155a718dc459e4b8f70744f2da1aa15206ec1df384414b5dde4fa115dc6bb3ff`.
The inventory hashes each record in directory order, using the zero-based
index, name, uncompressed length and stream SHA-256 separated by NUL,
with a newline after each record. Both OLE payload slots and the model
license slot contain four zero bytes. Relationships target streams within
the document. The preview images and the three keyed stores carry part,
configuration and dimension data. The decoded inventory contains no
embedded executable, installer or packaged attachment signatures.
[Research artifact policy](../../../Documentation/Reference/Research/ResearchArtifacts.md)

| Queue input | SHA-256 |
| --- | --- |
| [Native CAD fixture](../v2026/corpus/part-properties/CircularProperties.SLDPRT), 66,367 bytes | `1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23` |
| [Native advanced-manager control](../v2026/corpus/ladder/L1_boss.SLDPRT), 56,249 bytes | `55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6` |
| [Original SDK worker](https://github.com/TryUniCAD/Kit/blob/57ad014680b71273557b3635125ee004bedec29d/tests/Convert/Solidworks/Properties/ReadLiteralPart.py) | `17ee722aaa83b21798e2412b3245faf8cbb9833c134431aaa8b5d661cebd57f2` |
| [Original queue test](https://github.com/TryUniCAD/Kit/blob/57ad014680b71273557b3635125ee004bedec29d/tests/Convert/Solidworks/Properties/LiteralTextTests.py) | `f8d8ef7c8f76dcf8fb0d9a8a1a97da1fbe391a7fa5bbc99ce1db55aff07ca36c` |

The positive queue test checks all eight values, active configuration
ID 0 and the single solid through the normal strict SDK read. The
original negative test opened the ladder boss. Its 138-byte
`Contents/CusProps` has SHA-256
`9fd3dc57a5b385acbbd4b0f36fffec581481014616bb254a4f417f3537c1f036`.
The original process checked the active `Default` configuration and
solid B-rep, the property diagnostic and absence of all three text bags.
It verified strict conversion refusal with the destination intact.

Before the shared registry preflight, non-strict native conversion could
publish a document carrying the diagnostic. The earlier six-process
property receipt records its then-current scope using stdout SHA-256
`a82e966679a5c4b3471bc89993f14535fc9b300355bfd6889b45b978720694d7`.

## Legacy empty text compatibility

The [isolated wheel smoke](../../../tests/Convert/Runtime/IsolatedRuntime.py)
first converts the [legacy native control](../examples/.SLDPRT/example.SLDPRT),
SHA-256 `d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408`.
Its format-4 container uses archive version 18000. The summary, document
and configuration XML each have no authored text. Its complete manager
is the same 138-byte schema-one owner observed in the unrelated
version-19000 ladder control. Its digest is
`9fd3dc57a5b385acbbd4b0f36fffec581481014616bb254a4f417f3537c1f036`.
The independently observed shared body grammar supports the root,
keyed property container, file owner and cut-list owner. Every
legacy proof consumes the actual object bytes and validates the
empty owner graph and XML scopes. The rule requires the full wire
structure and does not depend on sample paths, lengths or hashes.
The reader checks concrete owner depth before reading fields. Only
the manager root, its keyed container and the two actual child
classes can open bodies.

The scoped legacy path preserves a strict SDK open with one solid,
one configuration and no optional text report. Older files with
authored text or unknown managers fail the optional projection.
The legacy queue case uses the exact wheel input for a strict JSON
conversion and adds one authored title to a separate in-memory input.
The wheel conversion succeeds with the prior model. The authored
title preserves the inspection model and produces the expected
write refusal. A separate binary case covers the malformed owner.
[Legacy queue case](../../../tests/Convert/Solidworks/Properties/LegacyTextTests.py)

## Binary-only owners and registry write policy

The reader validates a present `Contents/CusProps` independently of
XML. A proven empty binary-only manager leaves the document eligible
for ordinary conversion. An unsupported binary-only manager preserves
geometry and feature history with the optional text diagnostic.

The focused binary case replaces the legacy keyed container's runtime
class in a temporary in-memory package. The diagnostic retains the
`moCusPropMgr_c` schema path, fields `f20` and `f20/o`, byte offset 56
and the underlying unsupported-owner placement cause. The other two
variants preserve their original 138-byte and 33-byte binary managers
and omit all property XML. The advanced case refuses and the compatible
empty case converts. Each variant matches its original B-rep, bodies,
features, parameters, sketches and support planes.
[Binary queue case](../../../tests/Convert/Solidworks/Properties/BinaryTextTests.py)
· [Binary-only gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Properties/PropertyManagerCanStandAlone.md)

The shared registry write preflight rejects SOLIDWORKS part documents
with the explicit unsupported-text status. Strict and non-strict
conversion, compatibility conversion, public document writing and
direct registry writing agree. The error includes the original cause.
The stream probes keep their initial bytes and cursor. The implicit
path case creates no destination. The registry's ordinary target
transfer and carrier checks continue to apply to eligible documents.
[Write queue case](../../../tests/Convert/Solidworks/Properties/WriteTextTests.py)

For a snapshot already read by the registered interchange JSON reader,
the registry uses the actual input adapter for the text publication
decision. A matching interchange JSON writer can retain the original
document, unavailable diagnostic and source provenance. The same
status still refuses fresh SOLIDWORKS projections and direct writes.
The queue probes exercise both copy entry points and the complete
qualified circular-part JSON write/readback.
[Direct write queue case](../../../tests/Convert/Solidworks/Properties/LiteralTextTests.py)

The current host verification also reruns all six disclosed property
cases. Its fully absent control removes both the XML and binary
property owners. The advanced rectangle retains its real binary-only
manager in a separate refusal case. It repeats the byte-offset-103
owner-path diagnostic already present at review head
`57ad014680b71273557b3635125ee004bedec29d`. The older receipt records
the broader diagnostic before the owner-depth check. The other recorded
values and model comparisons reproduce.

The qualified circular part also succeeds through direct writes with
either carrier setting. Both results carry 11 transfer records and
preserve the three property bags, B-rep and feature timeline through
JSON readback. The neutral control continues through the same registry
preflight.
[Current revision-bound receipt](../measurements/2026/LiteralPartTextWriteScope01.json)

## Physical configuration validation remains open

A saved directory match and a nonempty `Contents/Config-0` establish
presence. A one-byte replacement can satisfy that presence check. The
complete version-19000 codec on revision
`8302c824a15830b837c72db75f79cabe5693d200` admits the two saved edits and
authored circular control by reading their actual ModelHeader and
consuming their entire Config-0. It writes identical Config-0 bytes on the
three source graphs. It refuses both a one-byte input and a valid prefix
missing the final byte for each source.

| Native input | Config-0 bytes | Config-0 SHA-256 |
| --- | ---: | --- |
| `PolygonSaved` | 26,085 | `0c18e5880e64c1ff1fef5560cd16e2b57c94a2545ad8ee73371ac79cc0bec631` |
| `CircleSaved` | 26,083 | `94e7079c568be9d3b6adf5b16215cf23d668f5f8dafe86462df218da86f9a8b4` |
| `CircleAuthored` | 26,055 | `5c78942508f55177db00ea7f394856a6d8c72683b19163b4e3d14e557fe045c7` |

`Archive/Config/ReadConfigMut.py` and `MakeConfigCtx.py` use the
existing `Archive/Header/ReadNativeHeader.py` and `HeaderRefNodes.py`.
The three walks enter `moPart_c` schema one, allocate the same header
`moExtObject_c` alias at slot 3 and reach map base 4 and final counter 122.
Each walk needs 38 concrete runtime class/schema pairs, 142 layout
entries in 24 rule modules, and 21 field operations. `moFeatColorTab_c`
uses schema zero. The concrete classes include part model data, atom,
mark record, relation and sketch block managers, views, units, lights,
material, visualization and exploded-view manager. Embedded owners add
annotation definitions, tables, transforms, and separate mass and
bounding-box caches. `Archive/Bodies/Layouts/Config/ModelFields.py` walks
both `moPart_c` sub-sections and uses contextual header references. An
outer byte count can detect a short stream while a complete decode also
checks the classes, field rules, backlinks and exact cursor exhaustion.

The direct aggregate read and ModelHeader imports span 170 SOLIDWORKS
modules. The measured base `76877b1c8b223f11ddf38c79dc10a2a878fc019e`
lacks 99 of them and their 11,089 lines. Excluding the
optional `Archive/Config/UsePartRelationsMut.py` mode and its resolved
sketch dependencies leaves 150 modules, 79 missing paths and 5,652 missing
lines. That narrower profile still needs the observed 142 layouts and
updates to main's `Archive/Bodies/Reading/ReadActions.py`,
`ReadNestedMut.py` and `ReadValueMut.py`. The physical configuration
finding remains open until the genuine codec can qualify this profile.
[Complete typed field and map evidence](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/ConfigBodyGrammar2026.md)

# Compatible part text projection on main

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
and name and requires the corresponding physical configuration and
resolved-feature streams. The valid directory is a prerequisite for
configuration XML. The separate full configuration manager and its
embedded value cache are outside this reader's property path.

XML goes through the SDK's existing untrusted parser after strict UTF-8
decoding and rejection of NUL and other encoding declarations. Its
document-type guard runs before interpretation. The text projection
keeps explicit names and values and refuses unmeasured variants,
expressions, populated managers and conflicting owners. Scope admission
is atomic. The output scheme keeps the same geometry and feature
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
| [Public SDK worker](../../../tests/Convert/Solidworks/Properties/ReadLiteralPart.py) | `854612c1c1d40b036675448f11a9191018332c2e62f8df47098d30c46d1c5fca` |
| [Queue test](../../../tests/Convert/Solidworks/Properties/LiteralTextTests.py) | `05d4b13b8b43930a2d3df1d1e81301e770fab28f03d51338af7fc278bf77248c` |

The test starts a fresh interpreter through the existing integration
suite. It checks all eight values, active configuration ID 0 and the
single solid through the normal strict SDK read. Execution awaits the
merge queue.

# D01 assembly document-property transport

Task `B04-SW2026-MATES-CONCENTRIC/source-property-transport` in PR #121,
owner `assembly_frontier`, base
`4f7ce7b398c7e2493f8fa4351190e30e41a7bc45`. The sources are the
disclosed SOLIDWORKS 2026 SP05.2 `34.5.2.0604` D01/D02/D03 states and
the A0, A1, A13 and A14 assembly controls. The scoped exit is a
complete property transport group derived from actual generated
property members and explicit application metadata.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Owned document properties](ConcentricD01PropertyOwners2026.md) ·
[21-stream baseline](ConcentricD01UserUnitTable2026.md)

## Complete shared transport profile

| Stream | Owned values and encoding |
| --- | --- |
| `[Content_Types].xml` | OPC package-level content types. The two default extension rows declare relationships and extended XML properties. Core and custom property overrides are present when their actual property streams are present. The native declaration is the shorter XML 1.0 form. |
| `_rels/.rels` | OPC root relationships with internal, package-relative targets. Generate unique IDs in the measured core, application and custom allocation order beginning at two. Emit present targets in the native application, core and custom order. Target and MIME type derive from the actual property roles. |
| `docProps/app.xml` | Extended application metadata. The modeled fields are template caption, whole edit minutes, application caption, company caption and application version. The observed ordinary profile has security zero and false shared-document and link flags. The common UTF-8 property writer escapes typed text and retains the native element order. |

The relationship and content-type vocabulary follows the published
Open Packaging Conventions. The observed SOLIDWORKS archive places
these XML documents in its existing native stream container. The
ordinary property group uses three root relationships. Its configuration
property XML and other auxiliary XML members have separate container
owners and produce no root relationship in this profile.
[ECMA-376 Parts 1, 2 and 4](https://ecma-international.org/publications-and-standards/standards/ecma-376/) ·
[Internal target and relationship ID rules](https://learn.microsoft.com/en-us/dotnet/api/system.io.packaging.package.createrelationship?view=windowsdesktop-9.0) ·
[Extended property types](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.extendedproperties.properties?view=openxml-3.0.1)

The writer checks the complete typed core or custom property XML
whenever that target is present. It derives the transport rows from
that verified membership. The reader checks every type and relationship
row, the complete application property sequence, and the actual
target inventory. The numeric slots are merely a deterministic
allocation policy for these measured roles. The investigation has
no evidence about other package relationship allocations.

## Saved controls and guarded composition

The six concentric before/after states and four independent assembly
controls each re-emit all three complete source streams exactly.
Their respective stream sizes are 556, 597 and 570 bytes. Source-only
application caption, company, template caption, original application
version and elapsed-time values are decoded for the comparison.
The receipt retains digests and numeric observations. The generated
model receives independent research application provenance and zero
authored prior edit minutes.

The original neutral geometric and chronology model stays exactly
as in the preceding unit proof. Two fresh stdin-only workers generate
identical 15,269-byte parents, SHA-256
`5317e0609a204953208d2ca0059ead999f91125e37314de4915dc13af7a836e9`.
They preserve all 21 preceding parent streams and the complete
cylinder child. The new manifests match the native 556-byte type index
and 597-byte root relationships. The 535-byte application member
contains the independently authored application metadata. Both builds
pass the prior mate, visual, chronology and property readback checks
with zero external accesses.

Three independently authored comparisons exercise application-only,
application plus core, and all three scopes. Their targets and
type declarations follow the actual membership. Unicode and ampersands
in the independently authored extended-property strings survive the
write and read. Changing the application metadata alone changes just
`docProps/app.xml` in the complete profile. The six refusal cases cover
a missing target, crossed relationship ID, foreign type declaration,
unsupported shared state, duplicate output and invalid edit minutes.
[Guarded receipt](../measurements/2026/ConcentricD01PropertyTransport01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01PropertyTransport.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

## Remaining source ownership

The original D01 parent still refuses `CheckAsmRoot`. The generated
parent has 24 streams, with 19 saved source members outside its modeled
inventory. The next linked index, `SwDocContentMgr/SwDocContentMgrInfo`,
decodes to `moBCModeInfo_c`, where the saved header clock and counter,
current configuration and actual selected occurrence records each have
different owners. The two D01 saves retain the same mate descriptor
while the component transforms and source path bindings change.
The complete mode flags and mate-descriptor field derivation remain
open. This transport proof does not cover that index, other native
integration or cache members, or any new native or held-out acceptance.

The [following content index proof](AssemblyContentIndex2026.md)
generates this complete member for the scoped D01 model. It also
reconstructs all eleven independently disclosed assembly indexes.

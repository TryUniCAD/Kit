# Normal SDK registry integration for ordinary owned planar assemblies

Task `B04-SW2026-ASSEMBLIES-C10/public integration`, owner `/root/assembly_occurrence`, delivery PR #121. This private overlay adds ordinary assembly dispatch to the existing public writer after the [disclosed private-registry native trial](SdkPortableAssemblyRegistryNative2026.md). Root owns publication, the native receipt and every Windows launch. No original A20/A21 payload, sealed source, native process or Git mutation was used here.

The native compiler and constructor bytes remain unchanged. The existing native trial opened, edited, rebuilt, saved child before parent, and freshly reopened the independently generated pair with healthy controls. This new boundary is qualified separately by reproducing both exact input files through the actual default `convert.write_document` registry at identical neutral inputs, encoded paths and writer epoch. It creates no new vendor trial or held-out credit. [Native receipt](../measurements/2026/SdkPortableAssemblyRegistryNative01.json) · [Default-entry process receipt](../measurements/2026/SdkDefaultAssemblyRegistration01.json)

## Registration and metadata

The existing reader exposes `solidworks.sldasm` as an alias of canonical `solidworks.sldprt`. Adding another canonical assembly writer conflicts with that namespace. The bounded change therefore keeps the existing `SldprtWriter` class and reader unchanged, adds an assembly-only branch to its selector/emitter, and gives that writer direction-specific metadata for `.sldprt` and `.sldasm`. The writer retains canonical `solidworks.sldprt`, alias `solidworks.sldasm`, six existing part capabilities and the three ordinary assembly capabilities. Drawing writing remains closed. [Alias namespace gotcha](../../../Documentation/Gotchas/Conversion/Registry/ReaderAliasesOwnTheWriterNamespace.md)

The part branch starts from exact staged writer SHA-256 `5f45f160895f84b9cb03c9ac9d2532e2c9425cf511ae45a0abc19ad3147531eb`. Both qualified circle modes and ordinary polygon behavior retain their existing dispatch and serializer. Reader classes, aliases, probe behavior and source implementations are unchanged.

Assembly admission uses the [portable compiler's](PortableAssemblyCompiler2026.md)
owned profile. It requires one dimensioned rectangular part definition, two
or three direct resolved occurrences, one fixed anchor, one configuration
per definition and an initially satisfied ordered group of aligned
coincident, parallel and positive driving distance mates selecting actual
principal-plane owners. Unsupported mates, curved children, nested
components, source references, hidden, suppressed or flexible instances,
unprojected data and incomplete ownership fail closed. Selection checks the
neutral shape. Recipe construction validates the complete graph before output.

## Paths and transaction boundary

Only a filesystem assembly destination is supported. The requested filename must equal the authored root name. Its single companion filename comes from the explicitly owned child's validated name. No existing external child file is read or resolved to generate output.

A real absolute Windows destination defines the native parent and sibling
identities. A macOS or Linux destination requires an explicit absolute
Windows `native_destination` mapping. Staged, final physical and native
basenames must agree. A separate no-CAD guest process exercises the native
Windows filesystem path directly.

Assembly overwrite is always rejected, including the shared staging layer's `final_overwrite` flag. Streams and arbitrary companion sinks are unsupported. Case-insensitive filename checks reject existing files, directories and dangling symlinks for either owned target. Normal SDK path staging completes the pair before publication and rolls back handled publication failures. A controlled second-publication failure preserved the pre-call state.

The initial 29-process result records a check-to-publication race in
the old shared stager. It deliberately creates a competing child and
observes its replacement. The updated stager publishes files exclusively
and tracks the identity of each output for rollback. The current regression
requires `FileExistsError`, preservation of the competing child and rollback
of the generated parent. [Controlled race and repair](../../../Documentation/Gotchas/Conversion/Commands/CompanionCreationCanRacePreflight.md)

## Exact process evidence

The frozen eight-file SDK dispatch manifest is SHA-256 `a564303f0bce24c74e00e1678d6b811a8b0bec1d6ad8b91534b667b643d8e2b4`. It pins the complete 4,237-file SDK closure and the prior compiler overlay. Private `Proof04/Result.json` SHA-256 is `9420119ab96b95d3d895c60d23e1de85f5180a4acfff5929b03db08fa4457b61`.

The initial 29 isolated processes cover default and explicit format
selection for two- and three-occurrence bundles, exact reproduction of the
native-tested pair, sixteen rejection and handled-failure cases, the old
publication race, and six standalone part comparisons. The current
29-process host replay checks preservation of the peer-created companion.
Polygon, Front diameter circle and reversed Top radius circle output bytes
and complete strict readback JSON match the exact standalone baseline.

At writer epoch `1794001000` and the original explicit native UNC identity,
the default and explicit routes reproduce parent SHA-256
`c6680b3c42c593e6f926031f24852b3e7e8d8a94f08748b19c7735da4440d92e` and child
`e0daf24884bcc664076bb02d00038afd96c414aa0e34a619b4d44b8571724ed2`.
These hashes identify the vendor-tested inputs. The parent is 10,833 bytes
and the child is 8,727 bytes. Result metadata reports one component file and
19,560 total bundle bytes.

Two separate Windows 11 processes verify direct local path selection and
the companion collision through the current transaction. The direct path
produces both files without a duplicate native mapping. The collision
keeps the peer file and rolls back the generated parent. Both have zero
runtime input reads and native application launches.

[Current host and Windows process receipt](../measurements/2026/SdkDefaultAssemblyPublication01.json)

Every writer interval recorded zero runtime input file reads and no
subprocess or CAD activation. The observer loads framework validation
imports before the construction audit. Normal validation runs inside
the public write call. Transaction policy enumerates directories and
writes the requested outputs. The Windows observer uses a portable
access mask to classify the platform's file-open events.

Black, Ruff, strict mypy, Pyright and repository steering pass for the eight SDK files. Focused integration modules invoke real fresh public processes for ordinary production CI. Remote CI, current-head review and publication remain root-owned and are not asserted here.

[Public API guide](../../../Documentation/Reference/Adapters/SolidworksAssemblyWriting.md) · [Change entry](../../../Documentation/Changes/Solidworks/Construction/Assembly/SolidworksPublicAssemblyWriting.md)

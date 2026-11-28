# SOLIDWORKS bare local import composer

`MakeBareImport` takes a neutral document with one supported planar
millimetre B-rep, explicit `PartBuildInput` settings, and `PartLabels`
that match the selected configuration. It returns the actual part,
feature, and atom identities alongside the shared archive graphs,
logical streams, and container bytes. Explicit literal part property
inputs use the existing summary, document, and configuration owners.
Extra document domains, unqualified configuration state and boss
presentation fields are refused.
[Package entry](../../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/MakeBareImport.py)

The composer attaches the actual native import feature to its generated
atom and rollback marks. It derives the local group key, keyword rows,
and both creation logs from those owners. The optional `AmbientValue`
accepts one explicit ambient `LightInput` for the current environment
owner. Omitting it preserves the empty environment.
[Bare prism profile](SolidworksLocalPrismTopology.md)

Two guarded offline comparisons reproduced seven complete research
candidates with all 87 logical streams byte for byte. The two authored
ambient candidates match earlier clean native input digests and their
individual stream hashes. The two empty-environment candidates match
earlier native inputs that opened with warning 32. At the same logical
path, supplying the light changes only the five observed graph and
header streams. The standalone package case had zero runtime input
reads and zero research builder imports. Twelve unsupported requests
were refused.
[Package comparison](../../../../re/solidworks/measurements/2026/BareImportPackage01.json)
[Prior clean lifecycle](../../../../re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json)
[Prior warning 32](../../../../re/solidworks/measurements/2026/GeneratedLocalImportWithoutLight01.json)
[Native same-locator lighting contrast](../../../../re/solidworks/measurements/2026/GeneratedLocalImportLightingContrast01.json)

These are offline package-composition results and exact comparisons to
earlier disclosed trials. Native qualification of additional cases and
public conversion admission remain separate.

# Feature color table requires schema zero

## Expectation

The SDK Config body profile can admit the feature color table with schema one,
matching its generic object constructor default.

## Actual behavior

The archive/document version and each runtime-class schema are separate fields,
as the existing [runtime-schema rule](../../RuntimeClassSchemasDiffer.md) describes.
The pinned 2026 `moFeatColorTab_c` runtime descriptor has schema zero. The first
SDK Config process sweep reproduced nine files and rejected three native child
parts because its concrete profile allowed only one for that class.

The native exported class record at `sldmfcu!0x3ce6d490` names
`moFeatColorTab_c`, has object size `0x10`, and stores zero at metadata `+0xc`.
The [descriptor evidence](../../../../../../re/solidworks/records/ConfigRuntimeDescriptors2026.json)
binds the original module and record hashes. This is static metadata inspection,
not a native application failure or acceptance result.

Abstract base records can instead use schema `0xffff`; their inherited field
layouts do not establish concrete tag admission. Some helper layouts do not
have an exported runtime descriptor at all.

## Workaround

Bind concrete schema admission to the actual registered current class metadata.
Retain the source descriptor when reading and writing that same graph. Keep
inherited/embedded grammar available independently of whether a class can occur
as a concrete object. Reject unsupported descriptor versions explicitly.
Do not change every object to schema zero or infer schema from document version.

The [Config grammar record](../../../../../../re/solidworks/records/ConfigBodyGrammar2026.md)
and [change entry](../../../../../Changes/Solidworks/Archive/Configuration/SolidworksTypedConfigurationGraph.md)
describe the bounded implementation and actual verification.

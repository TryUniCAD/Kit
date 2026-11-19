# An imported body reports BaseBody through COM

`IPartDoc::CreateFeatureFromBody3` creates an imported feature. On SOLIDWORKS
2026 SP05.2 build 34.5.2.0604, the returned feature has the tree name
`Imported1` and reports `BaseBody` from `IFeature::GetTypeName2`.
The source observer's initial expectation of `Imported` rejected the
feature after a successful rebuild between healthy controls.

Use the actual `BaseBody` type, the returned persistent feature identity
and the face-to-body ownership checks. The serialized class needs independent
archive evidence. [Source type receipt](../../../../../../re/solidworks/measurements/2026/ImportedBodyInitialType01.json) · [SOLIDWORKS 2026 import API](https://help.solidworks.com/2026/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IPartDoc~CreateFeatureFromBody3.html)

# Cold mate file reads can use the packaged child schema

An ordinary assembly file read uses the component's normal part reader
before binding the owned mate datums. On the disclosed cold rotated
assembly, both strict file read modes also touch the packaged
`RootLayout.json` structural schema. Guard it separately from the two
input CAD documents. The linked in-memory bundle reader resolves the same
cold data without that file access.
[Guarded checks](../../../../../../re/solidworks/measurements/2026/ColdRotatedMateRead01.json)

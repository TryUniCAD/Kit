# Large public FreeCAD assembly acceptance

The SOLIDWORKS research goal now includes a public, independently authored
FreeCAD assembly and its native part documents. The selected
[GA3D project](https://github.com/GA3Dtech/GA3D-basicbot-2023) has a 42.6 MB root
and 68 native documents. All source files are hash-locked to one publisher
revision before conversion. The lock records source links, file identities and
static document inventories. Publisher attribution and CERN-OHL-W-2.0 license
links are retained.

The [acceptance record](../../../re/solidworks/records/PublicAssemblyAcceptance2026.md)
defines the required source and output measurements, assembly and part
preservation, clean vendor inspection, dimension edits and save/reopen. Both
actual application screenshots must appear in the PR description with the
original CAD source link. A source render, codec round trip or screenshot alone
does not establish conversion acceptance.

Verification at this revision is source acquisition over HTTPS, Git-blob and
SHA-256 checking, and static XML inventory. Conversion, native measurements and
the two screenshots remain pending. No local tests were run. The production
SOLIDWORKS adapter remains read-only.

`re/tooling/sw2026/CaptureFreecad.py` runs as an explicitly selected FreeCAD
macro. `KIT_PUBLIC_SOURCE_JOB` names a JSON job with `source`, `output` and
`assembly_module_path`. It opens the unmodified public native root using the
publisher's assembly proxy modules, records native geometry and object state,
and captures the real application window through Qt. It saves no CAD document,
records before/after source digests and closes only its own document/process.
This observes source geometry; it does not convert it or prove SOLIDWORKS
acceptance. Native capture results are recorded only after execution.

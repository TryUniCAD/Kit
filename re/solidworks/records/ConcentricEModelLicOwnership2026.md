# D01 eModel license ownership

Task `B04-SW2026-MATES-CONCENTRIC`, [PR #121](https://github.com/TryUniCAD/Kit/pull/121),
anchor `0e8673133c0c82152a80acab9b502b1a3990e329`. Exclude
`Contents/eModelLic` from neutral assembly construction. The member
represents the licensed native session's saved package classification.
It is outside Kit's neutral model and measured viewing scope.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Ownership

The [licensed static study](../../../Documentation/Changes/Research/Writers/SolidWorks/Metadata/SolidWorksEModelLicense.md)
established on build `34.4.1.1011` that `SolidStorage_c::SaveEModelsNode`
gets the licensed session package type and saves it to this member.
The eDrawings consumer treats it as license information. The separately
documented Header2 license flag is sibling session metadata. The
historical research serializer that takes that header flag has the
same ownership prerequisite. A caller-provided scalar or its repetition
across controls supplies no authority to synthesize it for a new file.

For the exact `34.5.2.0604` local installation, read-only PE inspection
confirmed `doccplu.dll` SHA-256
`ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8`,
1,052,248 bytes, with `SaveEModelsNode` exported at RVA `0x280c0`
and the package lookup imported. REA identity evidence is
`ev_7a0afe0c4e30a2cd0f4ebd352f23649732df28cfc8ea75e9cbcc872c1f9f7270`.
The direct producer call path here comes from the earlier exact-build
static study. SP05.2 PE metadata confirms the named boundary. It does
not establish how the consuming viewer applies the saved permissions.

## Assembly evidence

The [numeric receipt](../measurements/2026/ConcentricEModelLicOwnership01.json)
binds each complete input archive SHA-256. D01's original and native
edited saves each contain the same four-byte member. The disclosed
A07 empty, A08 single-occurrence and A09 repeated-occurrence assemblies
also contain it. The four-byte member is absent from the exact
measured, neutral-generated radial parent and present on its subsequent
native save. All six present members compare equal in this local sample.
The receipt stores sizes and equality counts without the member data or
its digest.

The [passing radial lifecycle](../measurements/2026/ConcentricRadialAssemblyNative01.json)
binds both parent digests and records four distinct native processes
with healthy controls on `34.5.2.0604`. Its qualification is SOLIDWORKS
model opening, rebuilding, editing, saving and reopening for that
generated pair. Retain the existing omission on this neutral recipe.
An intact native-to-native claim that includes this permission-owned
member has an uncovered field. Keep D01 whole-source admission gated.
Any requirement to provide viewer licensing metadata belongs to a
licensed vendor save.

The [assembly stream emitter](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/EmitAsmStreams.py)
and [common sidecar constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Metadata/MakeAsmCommon.py)
have no neutral route for this member. The [root admission guard](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/Model/CheckAsmRoot.py)
still rejects unprojected source domains. This audit adds no codec,
transfer, publication or viewer authorization.

## Reproduce the membership observation

From the checkout, pass one or more of the receipt's roles with the
matching original disclosed paths. The check emits role, presence and
decoded extent.

```sh
PYTHONPATH=src python3.14 -B - d01_source=/path/to/disclosed/file.SLDASM <<'PY'
from hashlib import sha256
from json import loads
from pathlib import Path
from sys import argv

from convert.adapters.solidworks.Container.Container import SldprtArchive

receipt = loads(Path("re/solidworks/measurements/2026/ConcentricEModelLicOwnership01.json").read_bytes())
for item in argv[1:]:
    role, path = item.split("=", 1)
    expected = receipt["cases"][role]
    archive = Path(path).read_bytes()
    assert sha256(archive).hexdigest() == expected["archive_sha256"]
    member = SldprtArchive.from_bytes(archive).get(receipt["stream"])
    extent = None if member is None else len(member)
    assert (member is not None, extent) == (expected["present"], expected["member_bytes"])
    print(role, expected["present"], extent)
PY
```

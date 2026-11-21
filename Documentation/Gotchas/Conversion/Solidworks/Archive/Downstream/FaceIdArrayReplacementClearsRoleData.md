# Replacing face ID arrays clears the embedded role owner

The semantic face constructor creates downstream role data early. Retaining that initial object through later inline-array installation gives the wrong construction lifetime.

Native installer `0x4b755540` replaces the array and deletes/clears `BEnt.f18`. Later indexed face calls recreate the embedded owner under the active downstream scope, then look up actual already allocated face-row IDs. These calls precede appending the current face row. The new current face cannot supply its own ID then, and the first constructor-stage role map is empty despite the owner being present.

Build from the actual array-replacement and allocation sequence. Preserve the distinction between present empty role data and absent owner. Do not populate constructor maps from future face rows or treat this prefix observation as a universal final saved map; later ambiguity and replacement have their own state transitions.

The [source checkpoint](../../../../../../re/solidworks/records/DownstreamFreshFaceRows2026.md) binds the installer, recreating helper, ID lookup and caller order. The [receipt](../../../../../../re/solidworks/measurements/2026/DownstreamFreshFaceSource01.json) is source-only.

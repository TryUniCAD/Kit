# Native keyword IDs need validation before name rebinding

The legacy SOLIDWORKS name scanner can correct a keyword ID from a unique
feature name. In a generated local import, it can replace a stale
disclosed source ID 26 with the generated object's actual ID 18.

Validate the original XML rows against the linked archive graph before
using normalized features to qualify the native index. Each role, name
and ID belongs to an actual same-document feature or manager. A missing,
duplicated or misattached row must fail the native index gate.

[Typed index and refusal evidence](../../../../../re/solidworks/records/ImportedNativeKeywordIndex2026.md)

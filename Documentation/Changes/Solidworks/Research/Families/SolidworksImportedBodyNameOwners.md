# Trace native import feature and body names

The [contrast inspector](../../../../../re/tooling/sw2026/imported_body_source/InspectImportedBodyContrast.py)
reads three hash-locked native sources and compares the actual local
storage key, the resolved feature name and the kernel body's name owners.

Eight fresh SP05.2 processes pass, including both controls. Two independent
host readers reproduce 21 linked streams. The feature label owns the
local storage key. The atom supplies the full explicit Unicode body name.
The [archive record](../../../../../re/solidworks/records/ImportedBaseBody2026.md#ordinary-subclass-producer-fields-and-name-owners)
classifies the ordinary import suffix. The
[compatibility-name gotcha](../../../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/ImportedBodyNamesUseSeparateOwners.md)
records the differing label in the measured kernel attribute.

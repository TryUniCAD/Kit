# Explicit absent configuration-manager names

The internal schema-one ordinary part manager constructor now accepts `ManagerInput(None, configs, current_index)` without allocating a `moNodeName_c`. Existing named defaults and public part preparation stay unchanged.

`ReadMgrName` preserves the difference between an absent name and an invalid empty name owner. `ReadMgrIntent` projects the bounded configuration-directory and actual current-object aliases to explicit constructor inputs. It does not admit all other fields in an original manager or enable a public unnamed-manager writer.

The [construction record](../../../../../re/solidworks/records/ConfigurationManagerOptionalName2026.md) binds exact-build native constructor/serializer evidence and the [35-process host receipt](../../../../../re/solidworks/measurements/2026/ConfigurationManagerOptionalNameProcess01.json). Four original CMgr streams re-emit exactly, all four existing named full-container hashes are preserved, eight strict public geometry/history comparisons pass and 23 malformed fixtures are rejected. Generated unnamed variants change only CMgr and have no new native lifecycle qualification.

See [usage and replay](../../../../Reference/Research/Solidworks/Construction/Configuration/ManagerIntent.md) and [the presence gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Configuration/ManagerAbsenceIsNotEmptyName.md).

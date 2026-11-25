# Circular rim fillet research packs

The [feature packs](../../../re/Fusion/RimFilletPack/README.md) provide executable writer and reconstruction cases with independent native measurements.
They cover 12 circular blind extrusions with a top constant-radius fillet, including six parameter holdouts.
Use the package replay commands with Python 3.14 and unused output directories.

## Verification and limits

At SDK `66d4f5b856833833bbf67fe62a61c3450d8dc76f`, all 48 initial native checks passed controls, geometry, feature health, edits and restoration.
All 12 generated files reconstructed byte-identically with matching native receipt bindings. All 24 initial files decoded at the typed-native layer.
Strict neutral decoding refused all 24 inputs. All 48 public conversion attempts refused.
Five native-saved files reconstructed; seven retained the four-byte snapshot-header refusal.
Five blocked reconstruction checks passed after user-authorized owned-session recovery.

Shared-suite process regressions cover construction, complete archive cycling and protected conversion. They have not run locally.
Current-head CI/review and merge-group acceptance remain separate evidence. Native depth-edit work and the bounded width repair continue.
No complete semantic recovery or editable cross-format conversion is claimed. SOLIDWORKS evidence establishes API health only.

Task `A08h-RimFillet20261125` is owned by Codex on `feat/native-conversion-campaign-20261125`.
Dependencies are the existing controller, typed codecs, source-free constructor and licensed personal CAD API.
The owning register links delivery after publication. PRs #121 and #297 retain their independent implementation scopes.

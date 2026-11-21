# Preserve selected-empty scope after a native save

The strict SOLIDWORKS reader now projects `first_creator` scope for the
verified saved rectangular Front-plane boss. It joins the active
configuration, first live feature, selected-empty scope word, sole output
atom and saved partition through their actual linked owners. The saved
body, editable sketch, driving parameters and source payloads are
retained. The active blind depth follows its actual D1 display even
when the inactive display keeps the pre-edit value.

Both selected-empty derivatives round-trip their scope through neutral
JSON. The paired all-scope saves, cold cases, earlier single-boss
contrast and explicit two-stock cut retain their existing readback.
The promotion covers the measured saved first-boss reader profile.

[Owner proof and exact replay](../../../../../re/solidworks/records/FirstCreatorSavedScope2026.md)

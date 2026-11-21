# Definition class declarations own map slots

A repeated native class declaration occupies another map slot even
when its name and schema match an earlier class. The ordinary
Definition writer declares each class once, then references its
existing slot. Replaying a repeated declaration through that writer
would shift the later object slots.

The bounded Definition reader checks for an existing descriptor before
adding a class. Use a class reference for each reuse. The process
comparison verifies exact replay of the canonical line-style stream and
refusal of an independently framed repeated declaration.

[Definition codec evidence](../../../../../../re/solidworks/records/SdkOrdinaryPartDefinition2026.md)

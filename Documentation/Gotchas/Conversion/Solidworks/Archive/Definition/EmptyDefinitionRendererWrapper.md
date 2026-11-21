# An empty renderer wrapper can be present in a saved part

## Expectation

A part with no renderer objects stores a zero renderer presence flag in `Contents/Definition`.

## Actual behavior

The two disclosed version-19000 saves set the flag to one. The renderer wrapper carries two signed words and an empty object list.

## Workaround

Read the flag and the object count separately. Preserve a supported empty wrapper when re-emitting that source. Construct branch absence for the fresh ordinary profile. [Measured fields and scope](../../../../../../re/solidworks/records/SdkOrdinaryPartDefinition2026.md)

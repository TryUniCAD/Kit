# Downstream lookup registration has its own clock

Fresh downstream part population samples a FILETIME before constructing its face and edge lookup records. These records share that packed clock. The ModelHeader update time and the downstream kernel allocation clock belong to separate events.

Derive the `uniqueIdInfo_c` high and low words from the cache construction event and keep the table key, vector ordinal, body atom and kernel node identifier in their own fields. [Source and replay](../../../../../../re/solidworks/records/DownstreamFaceRegistration2026.md)

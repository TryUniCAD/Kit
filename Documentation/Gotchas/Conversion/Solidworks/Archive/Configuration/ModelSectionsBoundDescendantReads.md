# Model sections bound descendant reads

A whole-stream cursor can make an oversized count, split tag or CString
look complete by reading bytes from the next model section. The current
ordinary part root uses independent size prefixes for its lightweight and
resolved sections.

Apply the active section's absolute end before decoding prefix extensions,
text payloads and nested records. Keep the archive map shared across the
boundary and resume the parent cursor only after exact child consumption.
Abandon the graph after an incomplete child body.

[Disclosed control boundaries and malformed contrasts](../../../../../../re/solidworks/records/ConfigSectionSlice2026.md)

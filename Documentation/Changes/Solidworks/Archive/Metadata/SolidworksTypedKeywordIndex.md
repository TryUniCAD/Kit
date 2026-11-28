# Model native part and assembly keyword indexes

The keyword codec now represents occurrence rows, explicit radius and
diameter text, fixed decimal displays and the empty sheet-metal marker
as typed values. It preserves the saved cut attribute order and native
framing when reconstructing a source index.

Ordinary and nested assembly writers use the shared codec. Each
occurrence keeps its own ID, name and linked child file stem. The
typed source comparison covers 211 disclosed version-19000 streams, and
43 generated assembly and child files remain byte-identical.
[Evidence](../../../../../re/solidworks/records/KeywordTypedCorpus2026.md)

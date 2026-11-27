# SOLIDWORKS annotation checks need the actual configuration prefix

The ordinary full annotation scene writer expects a sketch-block manager class already allocated before its view list. A generated part can contain the same default `*Top` annotation under `moPart_c.fa48` and omit that preceding manager. The ordinary scene writer then rejects the prefix even though the view body and list are valid in the generated part.

Start the extraction comparison from the actual typed class and object map. Emit the expected one-item list from the shared view base and annotation subtype grammar, then compare its bytes and allocator state with the typed source span. [Source-only Top extraction](../../../../re/solidworks/WriterResearch/TopAnnotationExtraction.md)

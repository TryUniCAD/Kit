# SOLIDWORKS Top annotation extraction

Run `python re/solidworks/WriterResearch/ExtractTopAnnotation.py Source.SLDPRT --evidence SourceEvidence.json` to extract one default Top annotation from an ordinary generation-19000 source. Standard output contains the typed `annotation_view` JSON that the research constructor accepts. The separate evidence file binds this result to the source and Config-0 digests and records the independent display state.

The extractor checks the active configuration identity across the named keyword row, the typed manager row and the physical configuration lanes. It requires the complete default Top record, without extra views, unavailable aliases or custom transforms. It extracts one annotation property from the source. Whole-document reconstruction and publication retain their separate requirements. [Extractor contract and replay](../../../../re/solidworks/WriterResearch/TopAnnotationExtraction.md)

Two disclosed vendor saves and the generated annotated part returned byte-identical annotation JSON. The verifier also exercised ten refusals for absent or unsupported views, aliases, and mismatched source or configuration identity. The vendor saves retained an additional display seed in their separate evidence. [Recorded source replay](../../../../re/solidworks/measurements/2026/VendorBlindBossTopAnnotationExtraction.json)

# SOLIDWORKS Top annotation codec

The SOLIDWORKS research serializer accepts a single default `*Top` annotation view in a generation-19000 `Config-0` list. Run `python re/solidworks/WriterResearch/VerifyConfigAnnotViews.py --top-only` for the source-free stream check. Supply independently authored `.SLDPRT` paths after `--top-only` to compare their typed spans and allocator maps. Run without the flag to replay the existing principal view controls.

The source-free check generated the 282-byte annotation list and read the following 164-byte model lists. It also checked that requesting two Top views leaves the writer untouched. Two independently authored files matched all annotation bytes, including the signed zero matrix entries, and reached the original following offsets and allocator maps. All 14 existing Front, Right and appended Top comparisons retained their prior digest.

The codec covers the saved default view with ID 200. Native API view counts may include built-in views outside its archive list. Whole-part synthesis, native acceptance, and the SDK writer boundary remain open for this presentation state. [Field grammar and verification](../../../../re/solidworks/WriterResearch/ConfigScene/Annotation.md)

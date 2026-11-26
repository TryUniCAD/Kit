# Extract the Top annotation intent from a source

```powershell
python re/solidworks/WriterResearch/ExtractTopAnnotation.py Source.SLDPRT --evidence SourceEvidence.json
```

The command reads the source in the strict SDK reader and uses its exact bytes and typed document for custody. The source must have only the physical Config-0 configuration, model header and resolved features lanes. The sole manager and explicit named keyword rows must agree on native ID 0, and the active neutral configuration must have ID `sldprt:configuration:0`. The output is the `annotation_view` object of the existing research schema. [Candidate request](TopAnnotationCandidate.md)

The typed part configuration must own the single view through `moPart_c.fa48`. The list, schema-1 view class and view object must use their own allocated slots. The two graph nodes must have only their respective direct incoming fields in Config-0 and its model header. The extractor generates the expected full list span from the existing typed grammar and compares the span and map. This covers the two compact poses and their exact binary64 words, absent linked collections, null component, plane and comment pointers, and default subtype scalars. [List field grammar](ConfigScene/Annotation.md)

For this exact Top role the native rows give the model components of each view axis. The axes in the existing interchange transform are `+X`, `+Z`, `-Y`, with zero origin. The neutral frame normalizes signed zeros in the axis components. The checked native matrix still contains the two negative zeros, recorded separately in the evidence.

The JSON on standard output contains only annotation intent. The separate evidence records the enclosing `nec8/fec0` display entries, `feb4` seed, and secondary display set as observed. The vendor saves carried a separate seed entry `199`, while the generated annotated contrast had an empty set. These are separate fields from the Top view and remain outside the research annotation request. [Offline replay](../measurements/2026/VendorBlindBossTopAnnotationExtraction.json)

Run the [extractor verifier](VerifyTopAnnotationExtraction.py) with the two disclosed vendor sources and the generated pair and request from [the candidate replay](TopAnnotationCandidate.md). Its `--help` lists the five inputs and a fresh scratch directory. The verifier applies the same command boundary to generated unsupported views and leaves their source files unchanged.

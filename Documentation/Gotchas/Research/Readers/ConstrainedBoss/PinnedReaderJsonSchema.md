# Reader JSON belongs to its SDK revision

A typed reader document can contain fields that an older checkout's JSON model does not accept. The complete strict design-only P03 documents from SOLIDWORKS reader revision `c0a401a607` reach the graph comparator's JSON preflight, then the candidate checkout's older model refuses `FeatureStep.__init__() got an unexpected keyword argument 'OutputBodyIds'`. Matching never begins.

Retain the original typed JSON and digests. For this research case, preload the reader revision's document model and codec in an isolated process and run the unchanged comparator with the same arguments. This separate invocation keeps the newer field and its unresolved status. It reported graph differences on the two original files. The ordinary comparator continues to refuse the mixed-version inputs. [Readback findings](../../../../Changes/Research/Encoder/ConstrainedBossSdkReadback.md)

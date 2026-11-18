# Qualified analytic circle part writing

The ordinary SOLIDWORKS part writer adds two millimetre profiles: a fixed-centre Front-plane diameter with a forward blind boss, and a fixed-centre Top-plane radius with a reversed blind boss. Existing polygon writing remains byte-identical.

Use the normal write_document entry point with the actual neutral document and a matching .SLDPRT basename. Binary destinations require explicit final_destination. Strict native transfer policy continues to report six native capabilities and no dropped/carrier state. The writer uses one creation/save event and the existing final-path selector, never a source CAD file or saved field program.

Both supports and actual emission apply the same complete owner/parameter/constraint/end profile gate. Other circle profiles and unmodeled properties, expressions, materials, provenance, topology/payload data or additional document domains are rejected before output commit. Assembly/drawing writing is not enabled.

The original source/generated native qualification passed fourteen fresh processes and 400 numeric checks with healthy controls. The local integration proof passed 84 process calls, 76 public writes, ten circle/settings cases, two polygon before/after comparisons, 39 rejections and 100 typed stream round trips. A final focused test replay after a required test-only helper split passed eight more public writes. Frozen H01/H02 hashes are unchanged; construction and writer model-file reads are zero. All eleven Python files pass the final static gates.

[Native qualification](../../../../re/solidworks/measurements/2026/SdkOriginalCircleNative01.json), [integration record](../../../../re/solidworks/records/SdkCirclePublicRegistration2026.md), and [source-bound process receipt](../../../../re/solidworks/measurements/2026/SdkCirclePublicRegistration01.json) define the measured boundary.

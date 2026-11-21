# Guarded public read needs code preload

Preloading the adapter does not load every normal public-reader code dependency.
`InferCaps` imports `DocumentProvenance.HasProvenance` and
`DocumentWalk.WalkDocuments` lazily. The walk imports
`DocumentBoundary.GetDocument`; the reader's retained-source semantic hash also
reaches the lazy `DocumentIo.ToJson` import.

The first independent SDK bridge replay correctly rejected the first such code
open inside the strict runtime read guard. It stopped before any model input-file
read. This is an incomplete process proof, not a native load failure or evidence
that the guard should permit source/model files during construction.

The bridge process now imports these four reached code dependencies before
`AUDIT.BeginBuild`. The guard policy, input boundary, SDK implementation and
original failed snapshot remain unchanged. Preload code dependencies explicitly;
do not weaken the guard, execute a hidden warm-up model or classify a failed
replay as passing.

The corrected independent replay passed both guarded processes with zero runtime
input reads. The [bridge record](../../../../../../re/solidworks/records/SdkPlainPartAdapterBridge2026.md)
and [receipt](../../../../../../re/solidworks/measurements/2026/SdkPlainPartPreparation01.json)
bind the virgin rejected source closure, causal retry and complete observed result.

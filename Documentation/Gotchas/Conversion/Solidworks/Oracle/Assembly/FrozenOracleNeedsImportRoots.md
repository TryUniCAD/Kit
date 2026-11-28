# A frozen oracle launch needs explicit import roots

An observer invoked by script path on Windows starts with its own directory
on Python's import path. It can load adjacent oracle helpers before failing
to load the SDK package from the separate frozen source tree. In the portable
assembly trial, `interchange` failed to import before SOLIDWORKS launched, even
though the exact SDK files were present and verified.

Use the pinned guest interpreter with an explicit import path containing
the verified snapshot's `src` directory and the frozen observer directory.
Verify the complete manifest before launching COM. Preserve the original
failure so build and launch errors remain distinct from native measurements.

[Portable assembly transport and native receipt](../../../../../../re/solidworks/measurements/2026/SdkPortableAssemblyRegistryNative01.json)

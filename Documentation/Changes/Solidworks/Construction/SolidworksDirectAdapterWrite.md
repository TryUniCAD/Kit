# Write through the SOLIDWORKS adapter

`SldprtAdapter().write(document, destination, options)` invokes the canonical SOLIDWORKS writer for its supported part, assembly or drawing profile. Pass typed `WriteOptions` for configuration, native paths or transfer requirements. The standard registry stages filesystem output and preserves the normal refusal behavior for unsupported models.

Two fresh guarded processes compared this method with `write_document` for one part stream and one planar assembly with its generated part. All three native documents matched byte for byte and both routes reported the same native usability and transfer status. The registry still exposes one canonical SOLIDWORKS writer. [Process receipt](../../../../re/solidworks/measurements/2026/SdkDirectAdapterWrite01.json)

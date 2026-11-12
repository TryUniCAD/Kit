# Thin universal Mach-O images before ranged disassembly

The installed `llvm-objdump` honored start/stop addresses for a thin arm64 image, but emitted the complete text section when those range options were used with `--arch=arm64` on the universal image.
The result looked like a bounded successful command while producing unrelated instructions and excessive output.

Extract the arm64 slice with `lipo -thin arm64` first, then disassemble that file without the universal-image architecture option.
Keep both original and thin-image digests, and distinguish unslid virtual addresses from offsets in the universal file.
The [header evidence extractor](../../../../re/Fusion/Reconstruction/HeaderGrammar/InspectHeader.py) uses this method.

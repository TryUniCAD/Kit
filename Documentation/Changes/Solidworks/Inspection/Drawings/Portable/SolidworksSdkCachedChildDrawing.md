# Generate a linked drawing with a computed child cache

The SOLIDWORKS research tool constructs a Front drawing view, a native rectangular boss with its producing sketch, and a part with generated downstream face and edge identities. It links the drawing to the exact generated part and produces both files in the chosen output directory.

Run PrepareSdkCachedDrawing.py with a new output directory, the intended absolute Windows location and the independently authored light settings. Two guarded runs agree byte for byte with zero extra file accesses. The generated view survives native open with its saved solid, rebuild, movement, save and fresh reopen. Both pristine controls pass. The native result leaves the specific cache lookup unobserved. [Construction and verification](../../../../../../re/solidworks/records/SdkCachedChildDrawing2026.md)

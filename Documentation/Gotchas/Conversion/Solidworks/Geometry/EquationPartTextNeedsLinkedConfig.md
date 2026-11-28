# Read part text on the equation-aware configuration

Ordinary part text comes from the package's property streams. The public reader still requires a complete version-19000 configuration before attaching it. A generic configuration pass refuses a populated local equation at `moRelation_c` schema 1, even when the text streams and the fully typed equation are both readable.

Pass the physical configuration graph that already resolved the equation and actual part owners to the property reader. Keep the exact configuration gate for ordinary parts and the existing refusal for malformed text. [Guarded comparison](../../../../../re/solidworks/records/SdkC130PadPresentation2026.md)

# Downstream attribute slot zero carries six words

The SOLIDWORKS kernel registers both downstream definitions with three integer slots. The setter writes six integers into one array in slot zero. The two other slots can stay null for the generated ordinary part record.

Follow the kernel array layout when writing the attribute. Its owner key uses low word then high word. The downstream model-cache serializer writes the same key in high word then low word order, after the UUID string. [Native definition and generated checks](../../../../../../re/solidworks/records/GeneratedDownstreamPartition2026.md)

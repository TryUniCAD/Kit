# Appearance allocator JSON requires exact integers

An appearance allocator is an unsigned 64-bit integer stored on wire as two signed 32-bit words. Generic JSON tooling that passes every number through IEEE 754 binary64 can round large allocator values. The recorded decimal value `9223372043297226759` crosses that boundary and reads back as `(-2147483641, -2147483647)` when the request retains its exact integer. [Two-sided replay evidence](../../../../re/solidworks/measurements/2026/EmptyAppearanceReplay.json)

Keep the canonical request in an integer-preserving tool such as Python's JSON parser. Preserve the presence Boolean separately. Both an absent manager and a present empty manager can use value 1, but only the present manager stores allocator words. [Replay command and format](../../../../re/solidworks/records/ResavedRendererRead.md#replay-the-empty-allocator-in-a-fresh-definition)

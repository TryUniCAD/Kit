# Exact measured chamfer test inputs

These archives are generated from the disclosed neutral chamfer cases.
The stock-zlib replay reproduced the full archive SHA-256 values in the
[measured generation register](../../../measurements/2026/ChamferDistancePairGenerated01.json).
The [native measurements](../../../measurements/2026/ChamferDistancePairDisclosedNative01.json)
apply only to these exact bytes.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| EqualDistanceEdge.SLDPRT | 8990 | `3d550644a3c0730f3204794d923e7351a6d82c95782d4d6570ce55cf0d8ccded` |
| UnequalDistanceEdge.SLDPRT | 9174 | `e4fdfc9bf94e51fa2d6f0e2fd69e533539ce85f71f1a6283b119648fc7e696bb` |

The integration harness opens them as source files. It verifies all ten
logical streams against independent regeneration and checks byte-free JSON
republication under alternate compression. Product code does not load
these fixtures.

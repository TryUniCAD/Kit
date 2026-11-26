# P03 projected dimension order can differ from wire order

The public reader's constraint tuple might appear to follow the saved distance blocks. The pinned source and generated P03 candidate both store the width block before the height block, at the same recorded frame and scalar offsets. The strict design-only reader projects height then width for the source, and width then height for the candidate. Their individual dimension points and roles agree.

Retain the source tuple order and the physical distance order separately. The source projection comparator rejects the tuple mismatch. The current evidence does not justify changing the serialized distance order or removing the order check. [Exact readback findings](../../../Changes/Research/Encoder/ConstrainedBossSdkReadback.md)

# Equation sides own local token ranges

The stored right-side text in both disclosed width-to-depth equations begins with a space. Its equals token starts at zero, and the remaining token ranges index the side text after that leading space. The left side owns a distinct range starting at its own zero.

Use the measured side-local parser input to derive coordinates while preserving the stored side text. The width-to-depth replay validates each token against its own side and checks the actual dimension handles. Other equation grammar needs its own tokenization evidence. [Typed replay and field ownership](../../../../../../re/solidworks/records/PartEquationConfig2026.md)

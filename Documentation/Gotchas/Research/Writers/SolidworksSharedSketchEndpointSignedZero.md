# A shared sketch endpoint can have conflicting signed zeros

Ordinary float equality treats positive and negative zero as equal. An exact coordinate replay can therefore see a closed neutral loop even when adjacent lines specify different binary64 values for the same endpoint. The generated sketch allocates one shared point at that connection.

Before generating the shared point, compare the two endpoint words. The research replay refused a final endpoint with negative zero opposite a positive zero start. [Exact sketch coordinate guide](../../../../re/solidworks/records/VendorBlindBossExactSketch.md)

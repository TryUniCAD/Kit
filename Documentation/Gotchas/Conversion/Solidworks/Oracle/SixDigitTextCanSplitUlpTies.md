# Six-digit text can split a one-unit floating-point tie

Expectation: equal physical values within six-significant-digit precision always produce equal Python `.6g` text.

Actual behavior: the [capsule boss receipt](../../../../../re/solidworks/measurements/2026/CapsuleBossInspection01.json) contains two center-of-mass comparisons of `0.007273605` against the independent target `0.007273605000000001`. Their difference is one binary floating-point unit, `8.673617379884035e-19`, with relative error `1.1924784724884062e-16`. Six-digit formatting nevertheless produces `0.0072736` and `0.00727361` because the values straddle a decimal rounding tie.

Keep the original independent targets, actual measurements and declared numerical gates. Report relative/absolute error separately from rounded-text equality. This receipt retains all 304 original passing checks and independently verifies a maximum relative error of `5.680912614542858e-16`, with exact zero for zero targets. It also records 302 equal six-digit strings and the two disagreements; it claims no universal text identity. No native check, tolerance or target was changed to accept the result. Do not replace a target with an observed native value, clamp a measurement or hide the tie.

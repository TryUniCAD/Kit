# Native write guard imports can reenter the writer

The registry loads its write guards while the adapter packages are being
initialized. A guard that imports a SOLIDWORKS implementation module for
a marker can reenter the native writer before that guard is defined.

Put shared evidence markers in the adapter contract layer. Let both the
writer guard and the native reader import the same value. This keeps the
direct writer ready before it starts a file-free construction process.

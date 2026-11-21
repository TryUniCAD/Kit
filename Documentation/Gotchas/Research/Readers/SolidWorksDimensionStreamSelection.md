# solidworks dimensions can span two configuration streams

In the P04 cut-height edit, the two depths are stored in Contents/Config-0-ResolvedFeatures. Six sketch dimensions, including the equation-driven offsets, have their scalar records in Contents/Config-0. Scanning the resolved-feature stream alone therefore returns two of the eight measured dimensions. Look for the tagged name and scalar header in both streams and preserve each stream-relative offset.

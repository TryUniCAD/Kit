# Catalogue inference needs NumPy

An environment that can run the fixed archive reader may omit NumPy.
The catalogue field-inference worker imports NumPy before it evaluates the source pair.
On the Windows P03 probe, the missing package failed the assessment and left its eight rescans waiting.

Run catalogue comparisons with the repository's locked development dependency group.
Use the same interpreter for the catalogue and its supervisor workers.
The corrected Windows probe used Python 3.14.6 with locked NumPy 2.4.6 and completed all eight rescans.
[P03 catalogue replay evidence](../../../Changes/Research/Supervisor/Catalogue/CatalogueRescanThroughput.md#p03-catalogue-rescan-replay)

# Native rectangle arrays retain inactive slots

## Expectation

A rectangle with four lines returned by the native sketch API has four serialized points and four serialized line rows. Dropping inactive rows leaves an ordinary dense contour.

## Actual behavior

The disclosed 2026 `CreateCornerRectangle` stock reports four live API lines but retains eight point rows and five line rows in `sgSketch`. The live point slots are `0,1,6,7`; point slots `2,3,4,5` and the first line slot have `f54=5` and identity `-1`. Four actual unary axis constraints remain linked to the live lines.

The visible line endpoints still use the original array slots. Compacting the point array without translating every actual reference changes ownership. A reader that assumes all array rows are visible vertices also rejects or misreads the contour. Repeated coordinate values do not establish which row is active.

## Workaround

Preserve the typed rows, actual flags, handles and reference counts. Derive visible contour membership from independently bound entity state and real incidence. Use keyed original slot identities when projecting the four active vertices, preserve retired history separately, and keep unsupported state visible until its native rules qualify.

The [typed source record](../../../../../../re/solidworks/records/ThroughAllD01TypedRead2026.md) gives exact row/endpoint values. The [process receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllD01ReadProcess01.json) retains both saved states and the existing reader's rejection. This observation does not establish a universal rectangle row count or a constructor template.

# A DWG without its four header shorts stalls the drawing open

The DWG header section of a Fusion drawing ends with four BS values after its handle stream.
Each value uses the 2-bit `00` code and a full 16-bit short.
The remaining bits of the last byte follow the `0x55` fill pattern.
The ODA specification lists four unknown BS values at the end of the header variables.

Kit reads these bits as `TailWidth` and `TailBits` and writes them back unchanged.

| DWG                                         | `TailWidth` | Four values                       | Fill bits |
| ------------------------------------------- | ----------- | --------------------------------- | --------- |
| A1 control                                  | 77          | `0x8DA9`, `0xC9A5`, `0xF093`, `0xFED8` | `10101` |
| A2 control                                  | 77          | `0x7B4C`, `0xCEEE`, `0x05E7`, `0x8C61` | `10101` |
| 22 DWG exports of Fusion 2706.1.17          | 77          | Different in every export         | `10101`   |

The values do not follow from the DWG content alone.
`H1NoAcm` and `N2AuthoredF2d` carry the same DWG bytes.
Their Fusion exports still carry unrelated values, such as `0xBB79` and `0x1341` first.

Variants without the values stalled.

| Variant            | Header tail                                    | Result                                        |
| ------------------ | ---------------------------------------------- | --------------------------------------------- |
| `Q1NoDataStore`    | The A1 values and fill                         | Opened in 4.7 s with 3 views and 1 dimension  |
| `U1ZeroShorts`     | `Q1NoDataStore` with four zero values (`10` code) and zero fill | Not open after 453 s, no dialog |
| `F7ZeroHeaderTail` | The A1 control with no values and zero fill    | Not open after more than 10 minutes           |

Fusion checks the values themselves.
These variants change only the header tail of `Q1NoDataStore`.

| Variant              | Header tail                                         | Result                          |
| -------------------- | --------------------------------------------------- | ------------------------------- |
| `U9OwnShortsZeroPad` | The A1 values with zero fill bits                   | Opened in 3.3 s                 |
| `W2KitShorts`        | Four full values that Kit takes from the version GUID | Not open after 185 s, no dialog |
| `U2ForeignTail`      | The 77 tail bits of the A2 control                  | Not open after 181 s, no dialog |

Values from another Fusion save fail as well.
The values therefore belong to the file that Fusion wrote them into.

No standard checksum of a section, of the header area or of the whole file matches the values.
The tested functions were CRC-16 with three seeds, CRC-32, Adler-32 and the leading words of MD5, SHA-1 and SHA-256.
The values also match no word of the fingerprint GUID, the version GUID or the save timestamps.

Kit cannot write values that Fusion accepts.
Kit does not copy the values of a Fusion-saved file into an authored file.
Kit's authored shell writes four full BS values taken from the version GUID of the drawing.
A zero value becomes `0x5555`.
The header writer fills the last byte with the low bits of `0x55`.
Fusion 2706.1.17 therefore does not open a DWG that Kit authors, as the [authored shell gotcha](FusionDrawingAuthoredShell.md) records.

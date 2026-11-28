from dataclasses import dataclass as DataClass

from convert.adapters.base.WriteOptions import WriteOptions


# source and output bytes are bound to the same already measured part lifecycle
@DataClass(frozen=True, slots=True)
class BoxMeasure:
    SettingsValue: WriteOptions
    NativePath: str
    OutputDigest: str
    ByteCount: int
    TerminalDigest: str

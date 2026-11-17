from pathlib import Path as FilePath

from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt


# unqualified framing must remain visible instead of being swallowed by the promoted body codec
def MakeConfigTail(InputPath: FilePath) -> FilePath:
    Archive = SldprtArchive.from_bytes(InputPath.read_bytes())
    Streams = dict(Archive.streams)
    Streams["Contents/Config-0"] = Archive.require("Contents/Config-0") + bytes(2)
    OutputPath = InputPath.with_stem("ConfigurationWithTail")
    with OutputPath.open("xb") as Output:
        _ = Output.write(build_sldprt(Streams))
    return OutputPath

from dataclasses import replace as ReplaceValue
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawFile import (
    LinkedDrawFile,
)
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawInput import (
    LinkedDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Linked.MakeLinkedFile import (
    MakeLinkedFile,
)
from convert.adapters.solidworks.Drawing.Construction.Profiles.AttachOriginMut import (
    AttachOriginMut,
)
from convert.adapters.solidworks.Drawing.Construction.Profiles.RequireOriginChild import (
    NeedOriginChild,
)
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
    WriteNamedDef,
)


# one explicit origin display extends the existing complete linked constructor without changing its default output or public writer admission
def MakeOriginFile(
    InputValue: LinkedDrawInput, ChildValue: PartCandidate
) -> LinkedDrawFile:
    _ = NeedOriginChild(ChildValue)
    Candidate = MakeLinkedFile(InputValue, ChildValue)
    _ = AttachOriginMut(Candidate)
    StreamsValue = dict(Candidate.StreamsValue)
    StreamsValue["Contents/Definition"] = WriteNamedDef(Candidate.UiGraph).OutputValue
    return ReplaceValue(
        Candidate,
        StreamsValue=MappingProxyType(StreamsValue),
        BytesValue=BuildSldprt(StreamsValue),
    )

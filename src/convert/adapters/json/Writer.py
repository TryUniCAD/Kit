from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.base import Destination
from convert.adapters.base import WriteOptions
from convert.adapters.base import WriteResult
from convert.adapters.json.Metadata import KInfoValue
from convert.adapters.json.StreamIo import WriteStream
from convert.adapters.registry.EquationWrite import CheckEquations
from convert.adapters.registry.InchWrite import CheckInchWrite
from convert.adapters.registry.ResearchWrite import CheckResearch
from convert.adapters.registry.SupportWrite import CheckSupports
from convert.adapters.registry.NativeWrite import CheckNative
from convert.adapters.solidworks.Core.Preparation.Chamfers.MakeChmfSnap import (
    MakeChmfSnap,
)
from interchange import CadDocument
from interchange.Features.FeatureKinds import NativeFeature


# this mixin gives stream and filesystem destinations one writing policy
class JsonWriter:

    # the typed materials contract needs a shared interpretation so independent codecs retain consistent data contracts
    @property
    def TypedMaterials(self) -> bool:
        return True

    # this writer validates and emits deterministic utf eight json
    def EmitTarget(
        self,
        DocValue: CadDocument,
        Target: Destination,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        CheckResearch(DocValue)
        CheckInchWrite(DocValue)
        CheckEquations(DocValue)
        CheckSupports(DocValue)
        DocValue = CheckJsonNative(DocValue)
        Settings = Options or WriteOptions()
        if Settings.validate:
            DocValue.assert_valid()
        Payload = (DocValue.to_json() + "\n").encode("utf-8")
        if isinstance(Target, (str, FilePath)):
            Output = FilePath(Target).expanduser().resolve()
            if Output.exists() and not Settings.overwrite:
                raise FileExistsError(Output)
            Output.parent.mkdir(parents=True, exist_ok=True)
            _ = Output.write_bytes(Payload)
            return WriteResult(
                Output,
                KInfoValue.format_id,
                len(Payload),
                application_usable=True,
                vendor_loadable=True,
            )
        WriteStream(Target, Payload.decode("utf-8"), Payload)
        return WriteResult(
            None,
            KInfoValue.format_id,
            len(Payload),
            application_usable=True,
            vendor_loadable=True,
        )


# all nonnative rows still pass the shared writer guard after a chamfer is independently reverified
def CheckJsonNative(Document: CadDocument) -> CadDocument:
    Snapshot = MakeChmfSnap(Document)
    if Snapshot is None:
        CheckNative(Document)
        return Document
    CheckNative(
        ReplaceValue(
            Snapshot,
            feature_timeline=tuple(
                Value
                for Value in Snapshot.feature_timeline
                if not isinstance(Value.definition, NativeFeature)
            ),
        )
    )
    return Snapshot

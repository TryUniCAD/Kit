from collections.abc import Callable
from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from subprocess import CompletedProcess

from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import ConstraintRef


# edited relation operands must remain structurally valid to test identity rather than malformed json
def ChangeRules(InputDoc: CadDocument) -> tuple[CadDocument, ...]:
    SketchValue = InputDoc.sketches[0]
    Relations = SketchValue.constraints
    Perimeter = SketchValue.closed_profile_entity_ids[0]
    LocalCorner = next(
        Entity.id
        for Entity in SketchValue.entities
        if Entity.construction
        and not Entity.fixed
        and Entity.geometry == SketchValue.entities[-1].geometry
    )
    Changes = (
        (4, (ConstraintRef(Perimeter[1], "start"), ConstraintRef(Perimeter[1], "end"))),
        (4, Relations[4].references[::-1]),
        (10, (ConstraintRef(LocalCorner), Relations[10].references[1])),
    )
    return tuple(
        ReplaceValue(
            InputDoc,
            sketches=(
                ReplaceValue(
                    SketchValue,
                    constraints=Relations[:Position]
                    + (ReplaceValue(Relations[Position], references=Operands),)
                    + Relations[Position + 1 :],
                ),
            ),
        )
        for Position, Operands in Changes
    )


# an equally plausible span from another position cannot replace the selected sketch record
def ShiftOwnerSpan(InputDoc: CadDocument) -> CadDocument:
    Features = list(InputDoc.feature_timeline)
    Position = next(
        Index
        for Index, Feature in enumerate(Features)
        if Feature.sketch_id == InputDoc.sketches[0].id
    )
    OwnerValue = Features[Position]
    Provenance = OwnerValue.provenance
    assert Provenance is not None
    (SpanValue,) = Provenance.spans
    Features[Position] = ReplaceValue(
        OwnerValue,
        provenance=ReplaceValue(
            Provenance, spans=(ReplaceValue(SpanValue, offset=SpanValue.offset + 1),)
        ),
    )
    return ReplaceValue(InputDoc, feature_timeline=tuple(Features))


# the logical proof must reject wrong edges reversed operands and false source custody without creating output
def VerifyRefusals(
    RunIntent: Callable[..., CompletedProcess[str]],
    TmpPath: FilePath,
    SourceBytes: bytes,
    OutputPath: FilePath,
) -> None:
    Changed = TmpPath / "Changed.json"
    Refused = TmpPath / "Refused.json"
    InputDoc = CadDocument.from_json(SourceBytes.decode("utf-8"))
    Cases = [
        (CaseDoc, "P03 ordered constraint endpoints differ")
        for CaseDoc in ChangeRules(InputDoc)
    ]
    Cases.append((ShiftOwnerSpan(InputDoc), "P03 sketch owner span differs"))
    for CaseDoc, Message in Cases:
        _ = Changed.write_text(CaseDoc.to_json(), encoding="utf-8")
        Result = RunIntent(
            TmpPath, "prepare", "--input", str(Changed), "--output", str(Refused)
        )
        assert Result.returncode == 1 and Message in Result.stderr
        assert not Refused.exists()
    Retained = TmpPath / "RetainedSource.json"
    assert Retained.read_bytes() == SourceBytes
    for Existing in (Retained, OutputPath):
        Before = Existing.read_bytes()
        Result = RunIntent(
            TmpPath, "prepare", "--input", str(Retained), "--output", str(Existing)
        )
        assert Result.returncode == 1 and "P03 output already exists" in Result.stderr
        assert Existing.read_bytes() == Before

from dataclasses import replace
from hashlib import sha256
from math import isfinite
from os import fspath
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceBytesKey
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import CheckColdRead
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import ColdReadInput
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from interchange.document.Models.DocumentModel import CadDocument
from tooling.sw2026.PreparePlainPartEvidence import construct


def _part_locator(value):
    text = fspath(value)
    locator = PureWindowsPath(text)
    if not locator.is_absolute() or locator.suffix.casefold() != ".sldprt":
        raise ValueError("the candidate requires its absolute Windows .SLDPRT locator")
    return text


def _project_cold_source(document):
    if not IsColdRead(document) or document.brep_payloads:
        raise ValueError("SOLIDWORKS source requires a complete ordinary cold part readback")
    original = document.metadata.get(KSourceBytesKey)
    if type(original) is not bytes or sha256(original).hexdigest() != document.source.sha256:
        raise ValueError("SOLIDWORKS cold source bytes do not match the neutral source digest")
    archive = SldprtArchive.from_bytes(original, document.source.path)
    if ContainerMo(archive.streams) != KHeaderVersion:
        raise ValueError("SOLIDWORKS cold source requires the ordinary 19000 archive")
    header = ReadHeaderGraph(archive.require("Header2"), KHeaderVersion).FieldsValue
    locator = _part_locator(GetFileRef(header.get("f38")).PathValue)
    epoch = header.get("f70")
    if type(epoch) is not int:
        raise ValueError("SOLIDWORKS cold source lacks its typed creation epoch")
    authored = ColdReadInput(document, PureWindowsPath(locator).stem)
    regenerated = construct(authored, locator, epoch).BytesValue
    if regenerated != original:
        raise ValueError("SOLIDWORKS cold source does not exactly regenerate on this runtime")
    # Keep readback and its lazy SDK imports outside the construction audit.
    # The full source comparison covers the original scaffold, B-rep and custody.
    CheckColdRead(document, regenerated)
    return authored


def _depth_value(value):
    if type(value) not in (int, float):
        raise ValueError("the SOLIDWORKS depth edit must be a positive finite number in mm")
    try:
        depth = float(value)
    except OverflowError as error:
        raise ValueError("the SOLIDWORKS depth edit exceeds the millimetre domain") from error
    if not isfinite(depth) or depth <= 0.0:
        raise ValueError("the SOLIDWORKS depth edit must be a positive finite number in mm")
    return depth


def reconstruct(document, native_locator, *, depth_mm=None):
    """Return the authored request for exact candidate generation or SDK publication."""
    locator = _part_locator(native_locator)
    if type(document) is not CadDocument:
        raise TypeError("SOLIDWORKS reconstruction requires a CadDocument")
    if "kit.research_read_status" in document.metadata:
        raise ValueError("SOLIDWORKS reconstruction requires a qualified source read")
    if document.source.format_id == KPartFormatId:
        document = _project_cold_source(document)
        document = replace(document, metadata={"name": PureWindowsPath(locator).stem})
    original_plan = PlanPartWrite(document)
    if depth_mm is None:
        return document

    driver, = document.parameters
    boss, = document.feature_timeline
    length = replace(driver.value, value=_depth_value(depth_mm), unit="mm")
    changed = replace(
        document,
        parameters=(replace(driver, value=length),),
        feature_timeline=(replace(boss, definition=replace(boss.definition, length=length)),),
    )
    if PlanPartWrite(changed).DepthValue == original_plan.DepthValue:
        raise ValueError("the SOLIDWORKS depth edit must change the native driving value")
    return changed


def _construction_locator(native_locator, written_at):
    return RequirePartPath(_part_locator(native_locator), written_at).PathName


def _check_prepared_name(prepared, locator):
    name = prepared.metadata.get("name")
    target_name = PureWindowsPath(locator).stem
    if not isinstance(name, str) or name.casefold() != target_name.casefold():
        raise ValueError("the prepared SOLIDWORKS name differs from the native locator")


def prepare_generation_input(document, edit=None, *, native_locator, written_at):
    """Qualify the source and build a serializable ordinary part constructor input."""
    locator = _construction_locator(native_locator, written_at)
    depth = None
    if edit is not None:
        if (
            type(edit) is not dict
            or set(edit) != {"dimension", "value_mm"}
            or edit["dimension"] != "depth"
        ):
            raise ValueError("SOLIDWORKS supports only the absolute blind depth edit")
        depth = _depth_value(edit["value_mm"])
    prepared = reconstruct(document, locator, depth_mm=depth)
    _check_prepared_name(prepared, locator)
    return prepared


def generate_prepared_candidate(prepared, *, native_locator, written_at):
    """Construct an unmeasured part from a persisted constructor input."""
    locator = _construction_locator(native_locator, written_at)
    PlanPartWrite(prepared)
    _check_prepared_name(prepared, locator)
    return construct(prepared, locator, written_at).BytesValue


def generate_candidate(document, edit=None, *, native_locator, written_at):
    """Construct an unmeasured native candidate in memory for the research oracle."""
    prepared = prepare_generation_input(
        document, edit, native_locator=native_locator, written_at=written_at
    )
    return generate_prepared_candidate(
        prepared, native_locator=native_locator, written_at=written_at
    )

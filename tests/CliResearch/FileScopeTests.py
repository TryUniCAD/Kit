from tests.CliResearch.Reports.ReversalEvidence import VerifyReversal
from tests.CliResearch.Reports.ManifestEvidence import VerifyManifest
from hashlib import file_digest as FileDigest
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# a renamed real input must retain its byte identity and select experiments from its decoded features
def CheckFileScope(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = (
        RootPath
        / "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b/P04-fusion-termination-through-all.f3d"
    )
    InputPath = TmpPath / "unknown.bin"
    _ = InputPath.write_bytes(SourcePath.read_bytes())
    RunPath = TmpPath / "run"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(InputPath),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    Audit = LoadJson((RunPath / "FileScope.json").read_bytes())
    with InputPath.open("rb") as Stream:
        assert Audit["source_sha256"] == FileDigest(Stream, "sha256").hexdigest()
    assert Audit["member_count"] > 0 and Audit["unattributed_stream_ranges"]
    assert "family:extrude:cut-extrude" in Audit["selected_experiments"]
    assert "rRecipe" in Audit["native_classes"]["classes"][
        "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
    ]["fields"] and Audit["native_classes"]["classes"][
        "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
    ][
        "metatypes"
    ] == [
        "BrepRefMetaType"
    ]
    assert (
        "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
        not in Audit["reader_attempts"]["strict"]["message"]
    )
    VerifyManifest(RunPath)
    Timeline = LoadJson((RunPath / "Input-timeline.json").read_bytes())
    assert Timeline["oracle_fields_match"] is True
    assert [Feature["name"] for Feature in Timeline["components"][0]["features"]] == [
        "RectangleSketch",
        "BlindBoss",
        "CutSketch",
        "ThroughAllCut",
    ]
    Bodies = LoadJson((RunPath / "Input-body-measurements.json").read_bytes())
    assert Bodies["count_matches"]
    assert all(Bodies["bodies"]["Body1"].values())
    Changes = LoadJson((RunPath / "Input-repeat-save.json").read_bytes())
    assert Changes["status"] == "compared"
    assert len(set(Changes["controls"]) | {Audit["source_sha256"]}) == 3
    assert any(
        Field["field"] == "side1ExtentType"
        and (Field["control"], Field["input"]) == (1, 4)
        for Field in Changes["changed_after_repeat_filter"]
    )
    assert Audit["whole_file_verified"] is False
    Outcome = LoadJson((RunPath / "CatalogueResult.json").read_bytes())
    assert Outcome["status"] == "coverage_incomplete"
    assert Outcome["scopes"]["p04-through-all-body-selection"]["assessment_job"]


# equal volume pattern members require independent centroid matches through the public command
def CheckBodyIds(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = (
        RootPath / "re/Fusion/LocalOracle/FeatureAuthoring/Controls/BodyRectPattern.f3d"
    )
    RunPath = TmpPath / "pattern"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(SourcePath),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    Report = LoadJson((RunPath / "Input-body-correspondence.json").read_bytes())
    (Witness,) = Report["witnesses"]
    assert Witness["unique_geometry_match"]
    assert Report["default_name_rules"]["status"] == "needs_distinguishing_control"
    assert Report["default_name_rules"]["next_capture"] == "RemoveFirstDefaultBody"
    assert len(Witness["matches"]) == 6
    assert {
        (
            BodyValue["stored_name"],
            BodyValue["collection_ordinal"],
            BodyValue["vendor_name"],
        )
        for BodyValue in Witness["matches"]
    } == {("", Index, f"Body{Index}") for Index in range(1, 7)}


# spline records must survive serialization through the public native reader
def CheckLoftState(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = RootPath / "re/Fusion/LocalOracle/FeatureAuthoring/Controls/Loft.f3d"
    RunPath = TmpPath / "loft"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(SourcePath),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    assert (
        b"Journal.Spline.SplineNode.SplineNode"
        in (RunPath / "Input-native.json").read_bytes()
    )
    Timeline = LoadJson((RunPath / "Input-timeline.json").read_bytes())
    assert Timeline["capture_name_checks"][0]["ordered_names_match"]
    Measurement = Timeline["parameter_checks"][0]
    assert Measurement["all_names_match"] and Measurement["native_count"] == 2
    assert Measurement["fields"] == {
        NameValue: {"expression": True, "unit": True, "role": True, "value": True}
        for NameValue in ("d1", "d2")
    }
    Audit = LoadJson((RunPath / "FileScope.json").read_bytes())
    if (
        Audit["reader_attempts"]["native"].get("message")
        == "Unsupported Fusion semantic-state value"
    ):
        Evidence = LoadJson((RunPath / "Input-state-repair.json").read_bytes())
        assert Evidence["state_round_trip"] is True
        Patch = RunPath / "BrepTypes.patch"
        assert Patch.read_text() == Evidence["patch"]
        Applicable = RunProcess(
            ["git", "apply", "--check", str(Patch)],
            cwd=RootPath,
            capture_output=True,
            text=True,
        )
        assert Applicable.returncode == 0, Applicable.stderr


# held out parameter collections distinguish reported sweep roles from other saved bindings
def CheckSweep(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = (
        RootPath / "re/Fusion/Study/sweepnurbspaths-7ded30a4b9ae/polynomial_cubic.f3d"
    )
    RunPath = TmpPath / "sweep"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(SourcePath),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    Report = LoadJson((RunPath / "Input-timeline.json").read_bytes())[
        "parameter_projection"
    ]
    assert Report["status"] == "held_out_match"
    assert Report["predicted_visible_roles"] == [
        "AlongDistance",
        "TaperAngle",
        "TwistAngle",
    ]
    assert Report["other_saved_roles"] == [
        "AgainstDistance",
        "AgainstRailDistance",
        "AlongRailDistance",
    ]
    Digests = {Record["source_sha256"] for Record in Report["training"]}
    assert len(Digests) >= 2 and Report["held_out_sha256"] not in Digests


# an extensionless geometry stream must bind its recovered dimensions to the measured native archive
def CheckSnapshot(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Source = TmpPath / "unknown"
    _ = Source.write_bytes(
        (
            RootPath
            / "re/Fusion/LocalOracle/PrismSnapshot/OrdinaryRectangleSnapshot.smb"
        ).read_bytes()
    )
    Output = TmpPath / "run"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "auto",
            "--input",
            str(Source),
            "--directory",
            str(Output),
        ],
        capture_output=True,
        timeout=180,
    )
    assert Result.returncode == 2, Result.stderr
    Report = LoadJson((Output / "Input-raw-structure.json").read_bytes())
    assert Report["profile"] == "PrismSnapshot"
    assert Report["model"]["Model"] == {
        "Width": 40,
        "Depth": 30,
        "Height": 25,
        "BasePoint": [0, 0, 0],
    }
    assert Report["native_witness"]["geometry_matches"]
    assert Report["native_witness"]["observed"]["volume_cm3"] == 30
    assert (
        LoadJson((Output / "FileStall.json").read_bytes())["focus"] == "geometry_only"
    )


# the generated reader must apply cleanly and reproduce a second native solid through its own entry point
def CheckTorus(TmpPath: FilePath) -> None:
    from os import environ as ProcessEnvironment, pathsep as PathSeparator

    from zipfile import ZipFile as Archive

    RootPath = ResearchRoot()
    Folder = RootPath / "re/Fusion/LocalOracle/RoundBodies"
    Source = TmpPath / "unknown"
    with Archive(Folder / "vendor_DecodedPlacedTorus.f3d") as Document:
        (Member,) = [
            NameValue for NameValue in Document.namelist() if NameValue.endswith(".smb")
        ]
        _ = Source.write_bytes(Document.read(Member))
    Output = TmpPath / "run"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "auto",
            "--input",
            str(Source),
            "--directory",
            str(Output),
        ],
        capture_output=True,
        timeout=180,
    )
    assert Result.returncode == 2, Result.stderr
    Record = LoadJson((Output / "Input-reader-patch.json").read_bytes())
    Report = LoadJson((Output / "Input-raw-structure.json").read_bytes())
    assert Report["profile"] == "Torus" and len(Record["replayed_sha256"]) == 5
    assert Record["input_sha256"] not in Record["replayed_sha256"]
    assert Record["target_verification"] == "decoded_without_native_observation"
    assert Report["native_witness"] is None and not Report["missing_control_sha256"]
    _ = RunProcess(
        ["git", "apply", "--no-index", str(Output / "Reader.patch")],
        cwd=TmpPath,
        check=True,
    )
    Reader = TmpPath / Record["path"]
    with Reader.open("rb") as Stream:
        assert FileDigest(Stream, "sha256").hexdigest() == Record["reader_sha256"]
    Environment = {
        **ProcessEnvironment,
        "PYTHONPATH": PathSeparator.join(
            str(RootPath / EntryPath) for EntryPath in ("src", "re/automation")
        ),
    }
    Replay = RunProcess(
        [PythonPath, str(Reader), str(Folder / "AuthoredTorus.smb")],
        cwd=TmpPath,
        env=Environment,
        capture_output=True,
        check=True,
        timeout=60,
    )
    assert abs(LoadJson(Replay.stdout)["volumeCm3"] - 49.565153302270765) < 1e-9
    Refusal = RunProcess(
        [PythonPath, str(Reader), str(Folder / "AuthoredSphere.smb")],
        cwd=TmpPath,
        env=Environment,
        capture_output=True,
        timeout=60,
    )
    assert Refusal.returncode != 0


# a standalone journal must retain the prior empty state and independently match its companion snapshot
def CheckJournal(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Source = RootPath / "re/Fusion/LocalOracle/PlanarTopology/PlacedTetrahedron.smbh"
    Output = TmpPath / "journal"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "auto",
            "--input",
            str(Source),
            "--directory",
            str(Output),
        ],
        capture_output=True,
        timeout=180,
    )
    assert Result.returncode == 2, Result.stderr
    Report = LoadJson((Output / "Input-raw-structure.json").read_bytes())
    assert Report["profile"] == "PlanarJournal"
    assert Report["paired_geometry"]["oriented_boundaries_match"]
    assert Report["native_witness"]["geometry_matches"]
    States = {Record["state_id"]: Record for Record in Report["model"]["states"]}
    assert States[2]["bodies"] == [] and States[4]["active"]
    (BodyValue,) = States[4]["bodies"]
    assert (BodyValue["faces"], BodyValue["edges"], BodyValue["vertices"]) == (4, 6, 4)
    assert abs(BodyValue["volume_cm3"] - 3.945638020833335) < 1e-10


# raw stream discovery must withhold the evaluation family and verify the generated program at native scalar offsets
def CheckDimensions(TmpPath: FilePath) -> None:
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    RootPath = ResearchRoot()
    Folder = RootPath / "re/automation/PairedCaptures/P05"
    Target = TmpPath / "target"
    Control = TmpPath / "baseline"
    Member = "Contents/Config-0-ResolvedFeatures"
    for Pathname, Variant in ((Target, "edit-angle_deg-90"), (Control, "baseline-a")):
        PartPath = next(Folder.glob(f"solidworks-*/*{Variant}.SLDPRT"))
        _ = Pathname.write_bytes(
            SldprtArchive.FromBytes(PartPath.read_bytes()).Streams[Member]
        )
    Output = TmpPath / "run"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "auto",
            "--input",
            str(Target),
            "--control",
            str(Control),
            "--directory",
            str(Output),
        ],
        capture_output=True,
        timeout=180,
    )
    assert Result.returncode == 2, Result.stderr
    Report = LoadJson((Output / "Input-raw-structure.json").read_bytes())[
        "named_scalar_experiment"
    ]
    assert (Report["encoding"], Report["displacement"]) == ("<d", 22)
    assert {
        Record["recipe"]
        for Record in Report["trials"]
        if Record["split"] == "discovery"
    } == {"P01", "P03", "P04"}
    assert all(Record["generated_reader_matches"] for Record in Report["trials"])
    assert {Record["split"] for Record in Report["trials"]} == {
        "discovery",
        "qualification",
        "holdout",
    }
    assert len(Report["native_measurement_offsets"]) == 4
    Angle = next(
        Record for Record in Report["records"] if Record["name"] == "angle_deg"
    )
    assert Angle["offset"] in Report["native_measurement_offsets"]
    (Comparison,) = Report["control_replays"]
    Original = next(
        Record for Record in Comparison["records"] if Record["name"] == "angle_deg"
    )
    assert abs(Angle["value"] * 4 - Original["value"]) < 1e-12
    assert (Output / "Reader.patch").is_file()


# a reversed saved extrusion must agree with edited geometry and reject stale end positions
def CheckReversal(TmpPath: FilePath) -> None:
    from os import environ as ProcessEnvironment, pathsep as PathSeparator

    RootPath = ResearchRoot()
    RunPath = TmpPath / "research"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "auto",
            "--input",
            str(RootPath / "re/FreeCad/Verification/ReversedFrontEdited.FCStd"),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    VerifyReversal(RunPath)
    Graph = LoadJson((RunPath / "Input-edited-graph.json").read_bytes())
    Reader = LoadJson((RunPath / "Input-reader-patch.json").read_bytes())
    _ = RunProcess(
        ["git", "apply", "--no-index", str(RunPath / "Reader.patch")],
        cwd=TmpPath,
        check=True,
    )
    Generated = TmpPath / Reader["path"]
    with Generated.open("rb") as Stream:
        assert FileDigest(Stream, "sha256").hexdigest() == Reader["reader_sha256"]
    Replay = RunProcess(
        [
            PythonPath,
            str(Generated),
            str(RootPath / "re/FreeCad/Verification/ReversedFrontEdited.FCStd"),
        ],
        cwd=TmpPath,
        env={
            **ProcessEnvironment,
            "PYTHONPATH": PathSeparator.join(
                map(str, (RootPath / "src", RootPath / "re/automation"))
            ),
        },
        capture_output=True,
        check=True,
        timeout=90,
    )
    assert LoadJson(Replay.stdout) == Graph

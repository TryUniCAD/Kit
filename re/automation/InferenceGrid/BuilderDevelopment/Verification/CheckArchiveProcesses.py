# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# archive reader and writer witnesses must resolve to independently owned native session identities
def CheckArchiveProcesses(Check, Case, Report):
    Prefix = "report.cases." + Case["id"]
    Phases = Report.get("phases", {})
    Pids = {}
    for Name in ("first", "second", "third"):
        Owner = Phases.get(Name, {}).get("owner", {})
        Pid = Check.Field(Owner, "pid", "report.phases." + Name + ".owner")
        if type(Pid) is not int or Pid <= 0:
            Check.Add(
                "report.phases." + Name + ".owner.pid",
                "positive owned process id",
                Pid,
                "verifier_support_missing",
            )
            return
        Pids[Name] = Pid
    for Field, Name in (
        ("authoring_process_id", "first"),
        ("reopen_process_id", "second"),
        ("archive_reopen_process_id", "third"),
    ):
        Value = Check.Field(Case, Field, Prefix)
        if Value is not None:
            Check.Equal(Value, Pids[Name], Prefix + "." + Field, "unhealthy_session")
    Saves = Check.Field(Case, "saves", Prefix)
    Observed = Check.Field(Case, "observations", Prefix)
    Reopened = Check.Field(Observed, "reopened_files", Prefix + ".observations")
    if not isinstance(Saves, list) or not isinstance(Reopened, dict):
        return
    Archives = Report.get("archives", [])
    for Save in Saves:
        if not isinstance(Save, dict):
            continue
        Name, Role = Save.get("file"), Save.get("role")
        if Role not in {"baseline-a", "baseline-b", "edited"}:
            continue
        Writer = Pids["first"] if Role == "baseline-a" else Pids["second"]
        SavePath = Prefix + ".saves." + str(Name)
        RecordedWriter = Check.Field(Save, "writer_process_id", SavePath)
        if RecordedWriter is not None:
            Check.Equal(
                RecordedWriter,
                Writer,
                SavePath + ".writer_process_id",
                "unhealthy_session",
            )
        Matches = [
            Item
            for Item in Archives
            if isinstance(Item, dict)
            and Item.get("case_id") == Case["id"]
            and Item.get("role") == Role
        ]
        if len(Matches) == 1:
            ArchivedWriter = Check.Field(
                Matches[0], "writer_process_id", Prefix + ".archives." + Role
            )
            if ArchivedWriter is not None:
                Check.Equal(
                    ArchivedWriter,
                    Writer,
                    Prefix + ".archives." + Role + ".writer_process_id",
                    "source_mismatch",
                )
        Reading = Reopened.get(Name)
        if not isinstance(Reading, dict):
            continue
        ReadingPath = Prefix + ".reopened." + Name
        Reader = Check.Field(Reading, "process_id", ReadingPath)
        if Reader is not None:
            Check.Equal(
                Reader, Pids["third"], ReadingPath + ".process_id", "unhealthy_session"
            )
            if Reader == Writer:
                Check.Add(
                    ReadingPath + ".fresh_process",
                    "archive reopened outside its writer process",
                    {"writer_process_id": Writer, "process_id": Reader},
                    "unhealthy_session",
                )
        ReopenedWriter = Check.Field(Reading, "writer_process_id", ReadingPath)
        if ReopenedWriter is not None:
            Check.Equal(
                ReopenedWriter,
                Writer,
                ReadingPath + ".writer_process_id",
                "source_mismatch",
            )

from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Chronology.HeaderClocks import HeaderClocks
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeIntentHead import MakeIntentHead
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import RevisionBook
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionEvent import RevisionEvent
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionLog import RevisionLog
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.MakeSelfFile import MakeSelfFile
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import MakeMgrHeader
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevFeatMut import MakeRevFeatMut
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import ProjectRevolve
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import EmitRevStreams
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.MakeRevProfMut import MakeRevProfMut
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Container.Container import BuildSldprt


def explicit_book(system, settings, policy):
    stamp = settings.HeaderValue
    if policy == "coupled":
        events = (RevisionEvent("created", stamp.AuthorName, stamp.CompanyName, stamp.CreatedAt, stamp.CommentText),)
        return RevisionBook((stamp.AuthorName,), (stamp.CompanyName,), (RevisionLog(system.RootValue, system.RootValue.FieldsValue["f18"].FieldsValue["f08"], events),))
    first = settings.SystemValue.CreatedAt
    users = ("Chronology Alpha", "Chronology βeta")
    companies = ("Intent Studio", "Independent Studio")
    root = RevisionLog(system.RootValue, "Authored earlier model caption", (
        RevisionEvent("created", users[0], companies[0], first - 173, "Created"),
        RevisionEvent("modified", users[1], companies[1], first + 13, "Modified"),
    ))
    helper = next(value for value in system.FeatureValues if value.ClassValue.NameValue == "moCommentsFolder_c")
    notes = RevisionLog(helper, "Explicit helper chronology", (
        RevisionEvent("created", users[1], companies[0], first - 97, "Created"),
        RevisionEvent("modified", users[0], companies[1], first + 29, "Modified"),
    ))
    return RevisionBook(users, companies, (root, notes))


def compose(document, settings, policy):
    plan = ProjectRevolve(document)
    CheckPartInput(document, settings, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile, axis = MakeRevProfMut(system, settings, plan, allocator)
    feature, reference, end, angle = MakeRevFeatMut(system, profile, axis, settings, plan, allocator)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    book = explicit_book(system, settings, policy)
    created = settings.HeaderValue.CreatedAt
    clocks = HeaderClocks(created, settings.HeaderValue.ModifiedAt if policy == "coupled" else created - 86417, settings.HeaderValue.UpdatedAt if policy == "coupled" else created + 47)
    header = MakeIntentHead(system.RootValue, clocks, book, allocator, True)
    top = MakeIntentHead(system.RootValue, clocks, book, allocator, False)
    output = settings.OutputValue if policy == "coupled" else SelfFileInput(settings.OutputValue.PathName, created + 71)
    self_file = MakeSelfFile(system.RootValue, header, system.ConfigValues[0], output)
    header.FieldsValue["f38"] = self_file
    top.FieldsValue["f38"] = self_file
    headers = (header, top, MakeMgrHeader(system.ManagerValue, output.SavedAt))
    inputs = settings if policy == "coupled" else replace(settings, OutputValue=output, HistoryValue=replace(settings.HistoryValue, CreatedAt=created + 259))
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    features = (*system.FeatureValues, profile.ProfileValue, feature)
    streams, config, resolved = EmitRevStreams(system, features, headers, definition, inputs, plan)
    return {"bytes": BuildSldprt(streams, FormatVersion=4), "streams": streams, "headers": headers, "system": system, "profile": profile, "feature": feature, "plan": plan, "config": config, "resolved": resolved, "book": book, "clocks": clocks, "input": inputs, "allocator": allocator}

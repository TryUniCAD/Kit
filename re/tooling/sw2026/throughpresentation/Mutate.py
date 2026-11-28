from dataclasses import replace


def mutate(kind, model, link, nodes, foreign):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import (
        IndexFeatures,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
        ReadChildren,
    )
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
        ReadSingleNode,
    )

    by_class = lambda name: next(
        value for value in nodes.values() if value.ClassValue.NameValue == name
    )
    clone = lambda value: ArchiveNode(
        value.ClassValue,
        dict(value.FieldsValue),
        value.StartOffset,
        value.EndOffset,
        value.IndexValue,
    )
    remove = lambda ids: replace(
        model,
        features=tuple(value for value in model.features if value.object_id not in ids),
    )
    root = link.ConfigValue.RootValue
    cabinet, environment = by_class("moDetailCabinet_c"), by_class("moEnvFolder_c")
    stock, cut = by_class("moExtrusion_c"), by_class("moICE_c")
    stock_profile = tuple(nodes.values())[-4]
    if kind == "CopiedRoot":
        nodes[NativeNodeId(stock_profile)] = clone(stock_profile)
    elif kind == "CopiedMember":
        item = environment.FieldsValue["f60"]["list"]["items"][0]
        item["o"] = clone(item["o"])
    elif kind == "CopiedHelper":
        root.FieldsValue["f13f8"] = clone(root.FieldsValue["f13f8"])
    elif kind == "ForeignHelper":
        root.FieldsValue["f13f8"] = foreign.ConfigValue.RootValue.FieldsValue["f13f8"]
    elif kind == "StrippedPublicMember":
        model = remove({NativeNodeId(ReadChildren(environment)[0])})
    elif kind == "StrippedMembers":
        removed = {
            NativeNodeId(value)
            for owner in (environment, cabinet)
            for value in ReadChildren(owner)
        }
        for owner in (environment, cabinet):
            owner.FieldsValue["f60"]["list"] = {"n": 0, "items": []}
        model = remove(removed)
    elif kind == "StrippedHelper":
        model = remove({NativeNodeId(root.FieldsValue["f13f8"])})
        root.FieldsValue["f13f8"] = None
    elif kind == "ForeignEnvironment":
        root.FieldsValue["f1e0"] = foreign.ConfigValue.RootValue.FieldsValue["f1e0"]
    elif kind == "ForeignProfile":
        value = next(
            value
            for value in IndexFeatures(foreign).values()
            if value.ClassValue.NameValue == "moProfileFeature_c"
        )
        stock.FieldsValue["f60"]["list"]["items"][0]["o"] = value
    elif kind == "CopiedComponent":
        reference = stock_profile.FieldsValue["pd_f78"]
        reference.FieldsValue["f58"] = clone(reference.FieldsValue["f58"])
    elif kind == "CopiedDepth":
        end = stock.FieldsValue["f818"]
        end.FieldsValue["f18"] = clone(end.FieldsValue["f18"])
    elif kind == "CopiedScope":
        item = cut.FieldsValue["f548"]["items"][0]
        item["o"] = clone(item["o"])
    elif kind == "ForeignScope":
        foreign_cut = next(
            value
            for value in IndexFeatures(foreign).values()
            if value.ClassValue.NameValue == "moICE_c"
        )
        cut.FieldsValue["f548"]["items"][0]["o"] = ReadSingleNode(
            foreign_cut.FieldsValue["f548"], "moCompSolidBody_c"
        )
    elif kind == "UnusedCutDepth":
        cut.FieldsValue["f818"].FieldsValue["f18"] = stock.FieldsValue[
            "f818"
        ].FieldsValue["f18"]
    elif kind == "WrongEnd":
        cut.FieldsValue["f818"].FieldsValue["f0c"] = 0
    elif kind == "LostAxisRelation":
        dims = stock_profile.FieldsValue["pd_f80"].FieldsValue["dims"]
        dims["log_g1"].pop()
        dims["nlog1"] -= 1
    elif kind == "BrokenNotePair":
        head, tail = ReadChildren(cabinet)
        head.FieldsValue["f388"] = clone(tail)
    elif kind == "AuthoredLight":
        light = ReadChildren(environment)[0]
        name = light.FieldsValue["f18"]
        name.FieldsValue["f08"] = "AuthoredAmbient"
    elif kind == "ExtraFeature":
        value = replace(
            model.features[0], object_id=987654, name="unowned authored row"
        )
        model = replace(model, features=(*model.features, value))
    elif kind == "UnqualifiedVersion":
        link = replace(link, ConfigValue=replace(link.ConfigValue, VersionValue=18000))
    else:
        raise ValueError("unknown declared mutation")
    return model, link, nodes

# planned ownership and dependencies must not silently acquire verified support
def AddPlanItemMut(Rows, Entry, Kind, SourceId, ParentId=None):
    Details = {
        Name: Value
        for Name, Value in Entry.items()
        if Name not in ("id", "name", "subfeatures", "status")
    }
    for Value in Entry.get("status", {}).values():
        if Value != "unverified":
            raise ValueError("Feature plan cannot qualify support")
    Rows.AddItem(Entry["id"], Kind, Entry["name"], SourceId, ParentId, Details)
    for Index, Option in enumerate(Entry.get("options", [])):
        Rows.AddItem(
            Entry["id"] + "/option/" + str(Index),
            "feature_option",
            str(Option),
            SourceId,
            Entry["id"],
            {"domain_status": "unverified", "option": Option},
        )


# source links and observed name matches offer traceability without asserting executable mappings
def AddPlanRefsMut(Rows, Entry, SourceId):
    EntryId = Entry["id"]
    for Target in Entry.get("dependencies", []):
        if Target not in Rows.Items:
            raise ValueError("Unresolved plan dependency: " + Target)
        Rows.AddRelation(EntryId, Target, "planned_dependency", SourceId)
    for Anchor in Entry.get("api_anchors", []):
        TypeName = Anchor.get("type", "")
        Matches = [
            Row
            for Row in Rows.Items.values()
            if Row[1] == "api_type" and Row[2] == TypeName
        ]
        for Match in Matches:
            Rows.AddRelation(EntryId, Match[0], "declared_name_match", SourceId, Anchor)
        if not Matches:
            Rows.AddGap("planned_api_anchor_unobserved", SourceId, EntryId, Anchor)
    for RefId in Entry.get("source_ids", []):
        if RefId not in Rows.Sources:
            raise ValueError("Unresolved plan source: " + RefId)


# hierarchical plan records remain present when installed metadata exposes no matching interface
def AddPlanMut(Rows, PlanData, Digest):
    SourceId = "source:feature-plan"
    Rows.AddSource(
        SourceId,
        "feature_plan",
        "Sources/FeaturePlan.json",
        Digest,
        {"schema_version": PlanData["schema_version"]},
    )
    for Source in PlanData.get("sources", []):
        Rows.AddSource(
            Source["id"], "documentation_reference", Source["title"], "", Source
        )
    for Wave in PlanData.get("waves", []):
        AddPlanItemMut(Rows, Wave, "plan_wave", SourceId)
    for Family in PlanData["families"]:
        AddPlanItemMut(
            Rows, Family, "feature_family", SourceId, Family.get("parent_id")
        )
        for Feature in Family.get("subfeatures", []):
            AddPlanItemMut(Rows, Feature, "feature_subfeature", SourceId, Family["id"])
    for Family in PlanData["families"]:
        AddPlanRefsMut(Rows, Family, SourceId)
        for Feature in Family.get("subfeatures", []):
            AddPlanRefsMut(Rows, Feature, SourceId)
    for Gap in PlanData.get("gaps", []):
        Rows.AddGap(Gap["id"], SourceId, Details=Gap)
    Rows.AddGap(
        "planning_domains_unverified",
        SourceId,
        Details={
            "scope": "every family subfeature option and dependency is a proposed research obligation"
        },
    )

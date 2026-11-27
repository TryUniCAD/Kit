from datetime import date

from Project import graphql


def load_fields(token, project):
    rows = graphql(token, 'query($project:ID!){node(id:$project){... on ProjectV2{fields(first:100){nodes{... on ProjectV2Field{id name dataType} ... on ProjectV2SingleSelectField{id name dataType options{id name}}}}}}}', {"project": project["id"]})["node"]["fields"]["nodes"]
    fields = {row["name"]: row for row in rows if "name" in row}
    for name, field_id in project["Fields"].items():
        if name not in fields or fields[name]["id"] != field_id:
            raise ValueError("Configured project field does not match live metadata: " + name)
    if "Status" not in fields or fields["Status"]["dataType"] != "SINGLE_SELECT":
        raise ValueError("Native project Status field is unavailable")
    return fields


def publish_fields(token, project, fields, changes):
    if not 1 <= len(changes) <= 5:
        raise ValueError("A field publication batch requires one to five items")
    declarations = []
    mutations = []
    variables = {}
    expected = {}
    seen_items = set()
    for item_id, values in changes:
        if not isinstance(item_id, str) or not item_id or len(item_id) > 200 or item_id in seen_items:
            raise ValueError("Invalid or duplicate project item identity")
        seen_items.add(item_id)
        for name, value in values.items():
            if name not in fields:
                raise ValueError("Unknown project field: " + name)
            field = fields[name]
            if not isinstance(value, str) or not value or len(value) > 1024:
                raise ValueError("Project field values must be nonempty bounded strings")
            if field["dataType"] == "TEXT":
                typed = {"text": value}
            elif field["dataType"] == "DATE":
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError("Project dates must use YYYY-MM-DD")
                typed = {"date": value}
            elif field["dataType"] == "SINGLE_SELECT":
                if value not in {option["id"] for option in field["options"]}:
                    raise ValueError("Unknown single-select option for field: " + name)
                typed = {"singleSelectOptionId": value}
            else:
                raise ValueError("Unsupported project field type: " + field["dataType"])
            index = len(variables)
            alias = "f" + str(index)
            variables[alias] = {"projectId": project["id"], "itemId": item_id, "fieldId": field["id"], "value": typed}
            declarations.append("$" + alias + ":UpdateProjectV2ItemFieldValueInput!")
            mutations.append(alias + ":updateProjectV2ItemFieldValue(input:$" + alias + "){projectV2Item{id}}")
            expected[alias] = item_id
    if not variables:
        return
    if len(variables) > 75:
        raise ValueError("Project field batch exceeds 75 mutation operations")
    result = graphql(token, "mutation(" + ",".join(declarations) + "){" + " ".join(mutations) + "}", variables)
    if any(((result.get(alias) or {}).get("projectV2Item") or {}).get("id") != item_id for alias, item_id in expected.items()):
        raise ValueError("Field mutation outcome is uncertain; rescan remote fields before continuing")

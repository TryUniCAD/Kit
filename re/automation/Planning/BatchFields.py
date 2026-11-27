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

from graphlib import TopologicalSorter

from InferenceGrid.FeatureRoutes import FeatureRecipes


def OrderScopes(Catalogues, Scopes):
    Graph = {Scope: set() for Scope in sorted(Scopes)}
    for Catalogue in Catalogues.values():
        Families = Catalogue.get("families", {})
        FamilyScopes = {}
        for Identity, Entry in Catalogue["features"].items():
            Recipe = FeatureRecipes.get(Identity)
            if Recipe is not None and "family" in Entry:
                FamilyScopes.setdefault(Entry["family"], set()).add(Recipe.Scope)
        for Identity, Entry in Catalogue["features"].items():
            Recipe = FeatureRecipes.get(Identity)
            if Recipe is None:
                continue
            Pending = list(Entry.get("dependencies", ()))
            Seen = set()
            while Pending:
                Family = Pending.pop()
                if Family in Seen:
                    continue
                Seen.add(Family)
                Graph[Recipe.Scope].update(FamilyScopes.get(Family, ()))
                Group = Families[Family]
                Pending.extend(Group["dependencies"])
                if Group["parent"]:
                    Pending.append(Group["parent"])
            Graph[Recipe.Scope].discard(Recipe.Scope)
    for Scope, Identity in Scopes.items():
        Recipe = FeatureRecipes[Identity]
        Graph[Scope].update(
            Other
            for Other, OtherIdentity in Scopes.items()
            if FeatureRecipes[OtherIdentity].Recipe < Recipe.Recipe
        )
    return list(TopologicalSorter(Graph).static_order())

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
    Sequence = [Scope for _, Scope in sorted((FeatureRecipes[Identity].Recipe, Scope) for Scope, Identity in Scopes.items())]
    for Before, After in zip(Sequence, Sequence[1:]):
        Graph[After].add(Before)
    return list(TopologicalSorter(Graph).static_order())

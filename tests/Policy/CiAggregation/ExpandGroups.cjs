function ExpandGroups(Block, NativeCount) {
  const Dynamic = Block.match(
    /include: \$\{\{ fromJSON\(needs\.test-plan\.outputs\.native \|\| '([^']+)'\) \}\}/,
  );
  if (Dynamic) {
    if (![4, 5].includes(NativeCount))
      throw new Error("Invalid native fixture count");
    const Groups = JSON.parse(Dynamic[1]).map((Entry) => Entry.group);
    if (Groups.join(",") !== "shard-1,shard-2,shard-3,shard-4")
      throw new Error("Unexpected native matrix fallback");
    return Array.from(
      { length: NativeCount },
      (Value, Index) => `shard-${Index + 1}`,
    );
  }
  const Groups = [...Block.matchAll(/^\s+- group: ([\w-]+)$/gm)].map(
    ([, Group]) => Group,
  );
  if (!Groups.length) throw new Error("Unrecognized workflow group matrix");
  return Groups;
}

module.exports = { ExpandGroups };

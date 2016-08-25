function mtgfxns.isxformcard(card)
  -- TODO(JRC): Implement this function.
  return true
end

table.insert(mtgsets.${set_code}.draftrules.maxreqs, {mtgfxns.isxformcard, 1})
table.insert(mtgsets.${set_code}.draftrules.minreqs, {mtgfxns.isxformcard, 1})

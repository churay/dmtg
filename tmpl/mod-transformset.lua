function mtgfxns.isxformcard(card)
  -- TODO(JRC): Implement this function.
  return true
end

-- TODO(JRC): Reimplement all other functions to not recognize transform cards
-- as any rarity.

mtgsets.${set_code}.draftrules.maxreqs[1][2] = mtgsets.${set_code}.draftrules.maxreqs[1][2] - 1

table.insert(mtgsets.${set_code}.draftrules.maxreqs, {mtgfxns.isxformcard, 1})
table.insert(mtgsets.${set_code}.draftrules.minreqs, {mtgfxns.isxformcard, 1})

-- transform set mod --

function mtgfxns.isxformcard(card)
  return card.fid > 0
end

for _, maxreqpair in ipairs(mtgsets.${set_code}.draftrules.maxreqs) do
  local maxreqfxn = maxreqpair[1]
  maxreqpair[1] = function(card)
    return not mtgfxns.isxformcard(card) and maxreqfxn(card)
  end
end

mtgsets.${set_code}.draftrules.maxreqs[1][2] = mtgsets.${set_code}.draftrules.maxreqs[1][2] - 1

table.insert(mtgsets.${set_code}.draftrules.maxreqs, {mtgfxns.isxformcard, 1})
table.insert(mtgsets.${set_code}.draftrules.minreqs, {mtgfxns.isxformcard, 1})

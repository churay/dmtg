-- kaladesh mod --

function mtgfxns.isartifactcard(card)
  return string.match(string.lower(card.type), '%f[%a]artifact%f[%A]')
end

table.insert(mtgsets.${set_code}.draftrules.maxreqs, {mtgfxns.isartifactcard, 2})
table.insert(mtgsets.${set_code}.draftrules.minreqs, {mtgfxns.isartifactcard, 2})

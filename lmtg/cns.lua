function mtgfxns.isconspiracy(card)
  local isdraftcard = string.match(string.lower(card.rules), '%f[%a]draft%f[%A]')
  local isconspiracy = string.lower(card.type) == 'conspiracy'
  return isdraftcard or isconspiracy
end

table.remove(mtgsets.cns.draftrules.maxreqs)
table.insert(mtgsets.cns.draftrules.maxreqs, {mtgfxns.isconspiracy, 1})

table.remove(mtgsets.cns.draftrules.minreqs)
table.insert(mtgsets.cns.draftrules.minreqs, {mtgfxns.isconspiracy, 1})

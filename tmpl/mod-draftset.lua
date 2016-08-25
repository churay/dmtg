-- draft set mod --

function mtgfxns.isdraftcard(card)
  local isdraftcard = string.match(string.lower(card.rules), '%f[%a]draft%f[%A]')
  local isconspiracy = string.lower(card.type) == 'conspiracy'
  return isdraftcard or isconspiracy
end

table.insert(mtgsets.${set_code}.draftrules.maxreqs, {mtgfxns.isdraftcard, 1})
table.insert(mtgsets.${set_code}.draftrules.minreqs, {mtgfxns.isdraftcard, 1})

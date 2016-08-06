local function isconspiracy(card)
  local isdraftcard = string.match(string.lower(card.rules), 'draft')
  local isconspiracy = string.lower(card.type) == 'conspiracy'
  return isdraftcard or isconspiracy
end

table.remove(mtgsets.cns.draftrules.maxreqs, 1)
table.insert(mtgsets.cns.draftrules.maxreqs, 1, {isconspiracy, 1})

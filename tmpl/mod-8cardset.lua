-- eight card set mod --

mtgsets.${set_code}.draftrules.cardcount = 8

mtgsets.${set_code}.draftrules.maxreqs[1][2] = 6
mtgsets.${set_code}.draftrules.maxreqs[2][2] = function(r)
  if r <= 4/9 then return 2 elseif r <= 8/9 then return 1 else return 0 end
end
mtgsets.${set_code}.draftrules.maxreqs[3][2] = function(r)
  if r <= 4/9 then return 0 elseif r <= 8/9 then return 1 else return 2 end
end

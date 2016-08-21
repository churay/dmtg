mtgsets.${set_code} = {}

mtgsets.${set_code}.cards = {
  ${set_cards}
}

mtgsets.${set_code}.extras = {
  ${set_extras}
}

mtgsets.${set_code}.draftrules = mtgfxns.deepcopy(mtgsets.default.draftrules)

${set_mods}

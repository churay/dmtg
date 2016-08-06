mtgsets.${set_name} = {}

mtgsets.${set_name}.cards = {
  ${set_cards}
}

mtgsets.${set_name}.draftrules = deepcopy(mtgsets.default.draftrules)

${set_mods}

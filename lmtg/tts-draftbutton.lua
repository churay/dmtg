--[[ tabletop functions ]]--

function onload()
  self.createButton({
    click_function = 'draftcards',
    function_owner = self,
    label = 'Draft Cards',
    position = {0.0, 0.0, 0.0},
    rotation = {180.0, 0.0, 0.0},
    width = 450,
    height = 200,
    font_size = 80
  })
end

function draftcards()
  local draftset2objs = {}
  for setidx, setcode in ipairs(mtgdraft.setcodes) do
    if draftset2objs[draftset] ~= nil then
      draftset2objs[draftset] = mtgfxns.expanddeck(mtgdraft.carddeckobjs[setidx], -1)
    end
  end

  local draftbasepos = self.getPosition()
  local draftareabasepos = {x=draftbasepos.x-deckdims.w, y=1, z=draftbasepos.z-deckdims.d}
  local boostercount = #mtgdraft.setcodes * #getSeatedPlayers()
  local boostercolcount = 3

  local cardsgenerated = {}
  for boosteridx = 1, boostercount do
    local boosterrow = math.floor((boosteridx-1) / boostercolcount)
    local boostercol = (boosteridx-1) % boostercolcount
    local boosterpos = {
      x=draftareabasepos.x+boostercol*deckdims.w,
      y=draftareabasepos.y,
      z=draftareabasepos.z-boosterrow*deckdims.d
    }

    local boostersetidx = ((boosteridx-1) % #deckids) + 1
    local boostercardids = draftbooster(mtgdraft.settables[boostersetidx])
    for boostercardidx, boostercardid in ipairs(boostercardids) do
      local cardobj = draftset2objs[mtgdraft.setcodes[boostersetidx]][boostercardid]
      local cardclone = cardobj.clone({
        position={boosterpos.x, boosterpos.y+0.25*boostercardidx, boosterpos.z},
        snap_to_grid=false
      })
      cardclone.unlock()
    end
  end

  for _, setcards in pairs(draftset2objs) do
    mtgfxns.compressdeck(setcards)
  end
end

--[[ drafting functions ]]--

function draftbooster(settable, randomize)
  if randomize == nil then randomize = true end
  if randomize then mtgfxns.randomize() end

  local boostermaxreqs = mtgfxns.deepcopy(settable.draftrules.maxreqs)
  local boosterminreqs = mtgfxns.deepcopy(settable.draftrules.minreqs)

  -- NOTE(JRC): All requirements that have a function as their value determine
  -- their contents based on a randomness quotient supplied by the booster.
  -- The primary use for this is to determine whether the booster contains a
  -- rare or a mythic rare card.
  local boosterrandval = math.random()
  for maxreqidx, maxreqpair in ipairs(boostermaxreqs) do
    local maxreqfxn, maxreqval = maxreqpair[1], maxreqpair[2]
    if type(maxreqval) == 'function' then
      boostermaxreqs[maxreqidx][2] = maxreqval(boosterrandval)
    end
  end
  for minreqidx, minreqpair in ipairs(boosterminreqs) do
    local minreqfxn, minreqval = minreqpair[1], minreqpair[2]
    if type(minreqval) == 'function' then
      boosterminreqs[minreqidx][2] = minreqval(boosterrandval)
    end
  end

  local randomcards = mtgfxns.randomshuffle(mtgfxns.range(#settable.cards))
  local boostercards, randomcardidxidx = {}, 0
  while #boostercards < 15 do
    repeat
      randomcardidxidx = (randomcardidxidx%(#randomcards-#boostercards))+1
    until randomcards[randomcardidxidx] ~= -1
    local randomcardidx = randomcards[randomcardidxidx]
    local randomcard = settable.cards[randomcardidx]
    local cardmaxreqidxs, cardminreqidxs = {}, {}

    -- NOTE(JRC): In order to prevent wildcards from having arbitrary rarities,
    -- each matching max requirement is considered when determining whether or
    -- not a given card is 'maxed out'.
    local iscardmaxed = false
    for maxreqidx, maxreqpair in ipairs(boostermaxreqs) do
      local maxreqfxn, maxreqremaining = maxreqpair[1], maxreqpair[2]
      if maxreqfxn(randomcard) then
        table.insert(cardmaxreqidxs, maxreqidx)
        if maxreqremaining == 0 then iscardmaxed = true end
      end
    end

    -- TODO(JRC): Revise the 'isminrequired' calculation to use a greedy algorithm
    -- if impossible drafting situations are possible (only if there exists a subset
    -- of max that has an empty intersection with the set of one or more mins) and
    -- otherwise uses a non-greedy algorithm.
    local iscardmin, minrequiredcount = false, 0
    for minreqidx, minreqpair in ipairs(boosterminreqs) do
      local minreqfxn, minreqrequired = minreqpair[1], minreqpair[2]
      if minreqfxn(randomcard) then
        table.insert(cardminreqidxs, minreqidx)
        if minreqrequired ~= 0 then iscardmin = true end
      end
      minrequiredcount = minrequiredcount+minreqrequired
    end
    -- NOTE(JRC): In order to prevent impossible situations, all of the minimum
    -- constraints are satisfied before choosing any cards arbitrarily.
    local isminrequired = minrequiredcount > 0
    -- local isminrequired = 15-#boostercards <= minrequiredcount

    if not iscardmaxed and (not isminrequired or iscardmin) then
      for _, maxreqidx in ipairs(cardmaxreqidxs) do
        boostermaxreqs[maxreqidx][2] = math.max(boostermaxreqs[maxreqidx][2]-1, 0)
      end
      for _, minreqidx in ipairs(cardminreqidxs) do
        boosterminreqs[minreqidx][2] = math.max(boosterminreqs[minreqidx][2]-1, 0)
      end
      randomcards[randomcardidxidx] = -1
      table.insert(boostercards, randomcardidx)
    end
  end

  return boostercards
end

function testdraft(setcode)
  local settable = mtgdraft.settables[mtgfxns.getsetidx(setcode)]
  local draftbooster = draftbooster(settable, false)

  local draftcards = {}
  local draftcolors = {green=0, red=0, blue=0, white=0, black=0, colorless=0}
  local draftrarities = {c=0, u=0, r=0, m=0}

  for _, boostercardidx in ipairs(draftbooster) do
    local boostercard = settable.cards[boostercardidx]
    table.insert(draftcards, boostercard.name)

    if #boostercard.colors == 0 then
      draftcolors.colorless = draftcolors.colorless+1
    else
      for _, cardcolor in ipairs(boostercard.colors) do
        draftcolors[cardcolor] = draftcolors[cardcolor]+1
      end
    end

    draftrarities[boostercard.rarity] = draftrarities[boostercard.rarity]+1
  end

  function tabletostr(t)
    local st = {}
    for k, v in pairs(t) do table.insert(st, k .. ': ' .. v) end
    return '[' .. table.concat(st, ', ') .. ']'
  end

  print('booster summary:')
  print('    cards: [' .. table.concat(draftcards, ', ') .. ']')
  print('    colors: ' .. tabletostr(draftcolors))
  print('    rarities: ' .. tabletostr(draftrarities))
end

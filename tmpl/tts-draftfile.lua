--[[ draft rule functions ]]--

local function iscolor(color)
  return function(card)
    for _, cardcolor in ipairs(card.colors) do
      if cardcolor == color then return true end
    end
    return false
  end
end

local function island(card)
  local cardtype = string.lower(card.type)
  local isbasicland = cardtype == 'land'
  local isspecialland = string.sub(cardtype, -5) == ' land'
  return isbasicland or isspecialland
end

local function israrity(rarity)
  return function(card) return card.rarity == rarity end
end

--[[ utility functions ]]--

local function randomshuffle(list)
  local slist = {}

  for _, val in ipairs(list) do
    table.insert(slist, val)
  end

  for validx = 1, #list do
    local lastidx = #list-validx+1
    local randidx = math.random(lastidx)
    slist[randidx], slist[lastidx] = slist[lastidx], slist[randidx]
  end

  return slist
end

local function range(min, max, step)
  if max == nil and step == nil then min, max = max, min end
  local min = min or 1
  local max = max or 1
  local step = step or 1

  local rangelist, rangeiter = {}, min
  while rangeiter <= max do
    table.insert(rangelist, rangeiter)
    rangeiter = rangeiter + step
  end
  return rangelist
end

local function randomize()
  math.randomseed(os.time())
  for _ = 1, 3 do math.random() end
end

local function deepcopy(orig, copymt, _copied)
  if type(orig) ~= 'table' then return orig end
  if _copied and _copied[orig] then return _copied[orig] end

  local copied = _copied or {}
  local copy = copymt and setmetatable({}, getmetatable(orig)) or {}
  copied[orig] = copy
  for ok, ov in pairs( orig ) do
    copy[deepcopy(ok, copymt, copied)] = (deepcopy(ov, copymt, copied))
  end

  return copy
end

--[[ module data ]]--

local mtgsets = {}

mtgsets.default = {}
mtgsets.default.cards = {}
mtgsets.default.draftrules = {
  minreqs = {
    {iscolor('green'), 2},
    {iscolor('red'), 2},
    {iscolor('blue'), 2},
    {iscolor('white'), 2},
    {iscolor('black'), 2}
  },
  maxreqs = {
    {island, 1},
    {israrity('c'), 10},
    {israrity('u'), 3},
    {israrity('r'), function(r) return r <= 7/8 and 1 or 0 end},
    {israrity('m'), function(r) return r > 7/8 and 1 or 0 end}
  }
}

-- NOTE(JRC): This is where the script automatically populates the output
-- file with all of the set data.
${set_data}

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

-- TODO(JRC): Extend this logic so that multiple sets in a sequence can
-- be drafted.
function draftcards()
  -- TODO(JRC): Figure out a better way to determine the deck's GUID so that
  -- it can be retrieved in this function automatically.
  local deckid = '07a2fc'
  local deckset = mtgsets.${set_name}
  local deckobj = getObjectFromGUID(deckid)
  local deckdims = {w=2.5, h=0.25, d=3.5}

  local deckpos = deckobj.getPosition()
  local deckcopypos = {x=deckpos.x-deckdims.w, y=1, z=deckpos.z}
  local draftdeckpos = {x=deckcopypos.x-deckdims.w, y=1, z=deckcopypos.z}
  local draftareapos = {x=draftdeckpos.x, y=1, z=draftdeckpos.z-deckdims.d}

  randomize()

  -- TODO(JRC): Automatically determine the size of the deck and adjust
  -- the location of the drafting area accordingly.
  local deckcopy = deckobj.clone({deckcopypos.x, deckcopypos.y, deckcopypos.z})
  local deckcards= {}
  for cardidx = 1, deckcopy.getQuantity() do
    local cardobj = deckcopy.takeObject({
      position={draftdeckpos.x, draftdeckpos.y+0.25*cardidx, draftdeckpos.z},
      top=true
    })
    cardobj.lock()
    table.insert(deckcards, cardobj)
  end

  local boostercount = 3 -- 3 * #getSeatedPlayers()
  local boostercolcount = 3

  local cardsgenerated = {}
  for boosteridx = 1, boostercount do
    local boosterrow = math.floor((boosteridx-1) / boostercolcount)
    local boostercol = (boosteridx-1) % boostercolcount
    local boosterpos = {
      x=draftareapos.x+boostercol*deckdims.w,
      y=draftareapos.y,
      z=draftareapos.z-boosterrow*deckdims.d
    }

    local boostercardids = draftbooster(deckset)
    for boostercardidx, boostercardid in ipairs(boostercardids) do
      local cardobj = deckcards[boostercardid]
      local cardclone = cardobj.clone({
        position={boosterpos.x, boosterpos.y+0.25*boostercardidx, boosterpos.z},
        snap_to_grid=false
      })
      cardclone.unlock()
    end
  end

  for cardidx = #deckcards, 1, -1 do
    local cardobj = deckcards[cardidx]
    cardobj.destruct()
  end
end

--[[ drafting functions ]]--

function draftbooster(mtgset)
  local boostermaxreqs = deepcopy(mtgset.draftrules.maxreqs)
  local boosterminreqs = deepcopy(mtgset.draftrules.minreqs)

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

  local randomcards = randomshuffle(range(#mtgset.cards))
  local boostercards, randomcardidxidx = {}, 0
  while #boostercards < 15 do
    repeat
      randomcardidxidx = (randomcardidxidx%(#randomcards-#boostercards))+1
    until randomcards[randomcardidxidx] ~= -1
    local randomcardidx = randomcards[randomcardidxidx]
    local randomcard = mtgset.cards[randomcardidx]
    local cardmaxreqidxs, cardminreqidxs = {}, {}

    -- NOTE(JRC): In order to allow wildcards to have arbitrary rarities, only
    -- the first matching max requirement is considered when determining whether
    -- or not a given card is 'maxed out'.
    local iscardmaxed = false
    for maxreqidx, maxreqpair in ipairs(boostermaxreqs) do
      local maxreqfxn, maxreqremaining = maxreqpair[1], maxreqpair[2]
      if maxreqfxn(randomcard) then
        table.insert(cardmaxreqidxs, maxreqidx)
        if maxreqremaining == 0 then iscardmaxed = true end
        break
      end
    end

    -- NOTE(JRC): In order to prevent impossible situations, all of the minimum
    -- constraints are satisfied before choosing any cards arbitrarily.
    local iscardmin, minrequiredcount = false, 0
    for minreqidx, minreqpair in ipairs(boosterminreqs) do
      local minreqfxn, minreqrequired = minreqpair[1], minreqpair[2]
      if minreqfxn(randomcard) then
        table.insert(cardminreqidxs, minreqidx)
        if minreqrequired ~= 0 then iscardmin = true end
      end
      minrequiredcount = minrequiredcount+minreqrequired
    end
    local isminrequired = minrequiredcount > 0

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

--[[ debugging functions ]]--

-- TODO(JRC): Remove the following debugging code after more testing
-- is completed.
---[[
function testdraft()
  local draftset = mtgsets.${set_name}
  local draftbooster = draftbooster(draftset)

  local draftcards = {}
  local draftcolors = {green=0, red=0, blue=0, white=0, black=0, colorless=0}
  local draftrarities = {c=0, u=0, r=0, m=0}

  for _, boostercardidx in ipairs(draftbooster) do
    local boostercard = draftset.cards[boostercardidx]
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
--]]

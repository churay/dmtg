mtgsets = {}

-- TODO: Insert the contents of the data files for the relevant drafting sets
-- here to populate the 'mtgsets' table.
loadfile('../out/cns-out/magic-cns.lua', 'bt', {mtgsets=mtgsets})()

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
  local deckset = mtgsets.cns
  local deckobj = getObjectFromGUID(deckid)
  local deckdims = {w=2.5, h=1/4, d=3.5}

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

function draftbooster(mtgset)
  -- TODO(JRC): Determine whether or not to include a card as a particular
  -- color if it has more than one color (i.e. should red/black count as
  -- both a red and black card for minimum requirements).
  function iscolor(color)
    return function(card)
      for _, cardcolor in ipairs(card.colors) do
        if cardcolor == color then return true end
      end
      return false
    end
  end

  function island(card)
    return string.match(string.lower(card.type), '^.* ?land$')
  end

  -- TODO(JRC): Fix this so that land card requirements are treated
  -- separately from all of the other requirements (take the max
  -- requirement that applies first instead of all?).
  function israrity(rarity)
    return function(card) return not island(card) and card.rarity == rarity end
  end

  local randomcards = randomshuffle(range(#mtgset.cards))
  local israrebooster = math.random(8) ~= 1

  local boostermaxreqs = {
    [israrity('c')]=10,
    [israrity('u')]=3,
    [israrity(israrebooster and 'r' or 'm')]=1,
    [israrity(israrebooster and 'm' or 'r')]=0,
    [island]=1
  }
  local boosterminreqs = {
    [iscolor('green')]=2,
    [iscolor('red')]=2,
    [iscolor('blue')]=2,
    [iscolor('white')]=2,
    [iscolor('black')]=2
  }

  local boostercards, randomcardidxidx = {}, 1
  while #boostercards < 15 do
    local randomcardidx = randomcards[randomcardidxidx]
    local randomcard = mtgset.cards[randomcardidx]
    local cardmaxfxns, cardminfxns = {}, {}

    local iscardmaxed = false
    for maxreqfxn, maxreqremaining in pairs(boostermaxreqs) do
      if maxreqfxn(randomcard) then
        table.insert(cardmaxfxns, maxreqfxn)
        if maxreqremaining == 0 then iscardmaxed = true end
      end
    end

    local iscardmin, minrequiredcount = false, 0
    for minreqfxn, minreqrequired  in ipairs(boosterminreqs) do
      if minreqfxn(randomcard) then
        table.insert(cardminfxns, minreqfxn)
        if minreqrequired ~= 0 then iscardmin = true end
      end
      minrequiredcount = minrequiredcount+minreqrequired
    end
    local isminrequired = 15-#boostercards <= minrequiredcount

    if not iscardmaxed and (not isminrequired or iscardmin) then
      for _, cardmaxfxn in ipairs(cardmaxfxns) do
        boostermaxreqs[cardmaxfxn] = boostermaxreqs[cardmaxfxn]-1
      end
      for _, cardminfxn in ipairs(cardminfxns) do
        boosterminreqs[cardminfxn] = boosterminreqs[cardminfxn]-1
      end

      table.insert(boostercards, randomcardidx)
    end

    randomcardidxidx = randomcardidxidx + 1
  end

  return boostercards
end

function randomshuffle(list)
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

function range(min, max, step)
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

function randomize()
  math.randomseed( os.time() )
  for _ = 1, 3 do math.random() end
end

-- TODO(JRC): Remove the following debugging code after more testing
-- is completed.
--[[
function testdraft()
  t = draftbooster(mtgsets.cns)
  for _, v in ipairs(t) do
    print(v .. ':')
    for ck, cv in pairs(mtgsets.cns.cards[v]) do
      local cvstr = type(cv) == 'table' and '[ ' or tostring(cv)
      if type(cv) == 'table' then
        for _, cc in ipairs(cv) do cvstr = cvstr .. cc .. ', ' end
        cvstr = cvstr .. ']'
      end
      print('    ' .. ck .. ': ' .. cvstr)
    end
  end
end
--]]

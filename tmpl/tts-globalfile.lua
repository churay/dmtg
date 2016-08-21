--[[ global functions ]]--

mtgfxns = {}

-- utility functions --

function mtgfxns.randomshuffle(list)
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

function mtgfxns.range(min, max, step)
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

function mtgfxns.randomize()
  math.randomseed(os.time())
  for _ = 1, 3 do math.random() end
end

function mtgfxns.deepcopy(orig, copymt, _copied)
  if type(orig) ~= 'table' then return orig end
  if _copied and _copied[orig] then return _copied[orig] end

  local copied = _copied or {}
  local copy = copymt and setmetatable({}, getmetatable(orig)) or {}
  copied[orig] = copy
  for ok, ov in pairs( orig ) do
    copy[mtgfxns.deepcopy(ok, copymt, copied)] =
      (mtgfxns.deepcopy(ov, copymt, copied))
  end

  return copy
end

-- drafting functions --

function mtgfxns.iscolor(color)
  return function(card)
    for _, cardcolor in ipairs(card.colors) do
      if cardcolor == color then return true end
    end
    return false
  end
end

function mtgfxns.island(card)
  return string.match(string.lower(card.type), '%f[%a]land%f[%A]')
end

function mtgfxns.israrity(rarity)
  return function(card) return card.rarity == rarity end
end

function mtgfxns.getsetidx(setcode)
  for codeidx, code in ipairs(mtgdraft.setcodes) do
    if setcode == code then return codeidx end
  end
end

-- table functions --

-- TODO(JRC): Set the names of expanded cards here.
function mtgfxns.expanddeck(deckobj, expanddir=1)
  -- TODO(JRC): Automatically determine the size of the deck and adjust
  -- the location of the drafting area accordingly.
  local expanddir = expanddir < 0 and -1 or 1
  local deckdims = {w=2.5, h=0.25, d=3.5}

  local deckpos = deckobj.getPosition()
  local copypos = {x=deckpos.x, y=1, z=deckpos.z+expanddir*deckdims.d}

  local deckcopy = deckobj.clone({copypos.x, copypos.y, copypos.z})
  local deckcardobjs = {}
  for cardidx = 1, deckcopy.getQuantity() do
    local cardobj = deckcopy.takeObject({
      position={copypos.x, copypos.y+0.25*cardidx, copypos.z+expanddir*deckdims.d},
      top=true
    })
    cardobj.lock()
    table.insert(deckcardobjs, cardobj)
  end

  return deckcardobjs
end

function mtgfxns.compressdeck(deckcardobjs)
  for _, deckcardobj in ipairs(deckcardobjs) do
    deckcardobj.destruct()
  end
end

--[[ global data ]]--

-- card data --

mtgsets = {}

mtgsets.default = {}
mtgsets.default.cards = {}
mtgsets.default.draftrules = {
  minreqs = {
    {mtgfxns.iscolor('green'), 2},
    {mtgfxns.iscolor('red'), 2},
    {mtgfxns.iscolor('blue'), 2},
    {mtgfxns.iscolor('white'), 2},
    {mtgfxns.iscolor('black'), 2},
    {mtgfxns.island, 1}
  },
  maxreqs = {
    {mtgfxns.israrity('c'), 11},
    {mtgfxns.israrity('u'), 3},
    {mtgfxns.israrity('r'), function(r) return r <= 7/8 and 1 or 0 end},
    {mtgfxns.israrity('m'), function(r) return r > 7/8 and 1 or 0 end},
    {mtgfxns.island, 1}
  }
}

${draft_data}

-- draft data --

mtgdraft = {}

mtgdraft.setcodes = {${set_code_1}, ${set_code_2}, ${set_code_3}}
mtgdraft.settables = {
  mtgsets[mtgdraft.setcodes[1]],
  mtgsets[mtgdraft.setcodes[2]],
  mtgsets[mtgdraft.setcodes[3]]
}

-- TODO(JRC): Figure out a better way to determine the deck's GUID so that
-- it can be retrieved in this function automatically.
mtgdraft.carddeckobjs = {
  --[[
  getObjectFromGUID('123456'),
  getObjectFromGUID('123456'),
  getObjectFromGUID('123456')
  --]]
}
mtgdraft.extradeckobjs = {
  --[[
  getObjectFromGUID('123456'),
  getObjectFromGUID('123456'),
  getObjectFromGUID('123456')
  --]]
}

--[[ tabletop functions ]]--

function onload()
  -- TODO(JRC): Add functionality here if necessary.
end

function update()
  -- TODO(JRC): Add functionality here if necessary.
end

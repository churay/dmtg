--[[ global functions ]]--

local mtgfxns = {}

-- utility functions --

function mtgfxns.randomshuffle(list)
  local slist = {}

  for _, val in ipairs(list) do
    table.insert(slist, val)
  end

  for validx = 1, #list do
    local lastidx = #list - validx + 1
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

-- table functions --

function mtgfxns.getdeckdims()
  return {w=2.5, h=0.25, d=3.5}
end

function mtgfxns.getbagdims()
  return {w=2.5, h=1.0, d=2.5}
end

function mtgfxns.expanddeck(deckobj, expanddir)
  -- TODO(JRC): Automatically determine the size of the deck and adjust
  -- the location of the drafting area accordingly.
  local expanddir = (expanddir == nil or expanddir > 0) and 1 or -1
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

-- general data --

local mtgdata = {}

mtgdata.colors = {
  green = {147, 203, 164},
  red = {238, 164, 137},
  blue = {169, 220, 239},
  white = {249, 245, 208},
  black = {197, 190, 184}
}

-- card data --

local mtgsets = {}

mtgsets.default = {}
mtgsets.default.cards = {}
mtgsets.default.extras = {}
mtgsets.default.draftrules = {
  cardcount = 15,
  minreqs = {
    {mtgfxns.iscolor('green'), 2},
    {mtgfxns.iscolor('red'), 2},
    {mtgfxns.iscolor('blue'), 2},
    {mtgfxns.iscolor('white'), 2},
    {mtgfxns.iscolor('black'), 2},
    {mtgfxns.island, 0}
  },
  maxreqs = {
    {mtgfxns.israrity('c'), 11},
    {mtgfxns.israrity('u'), 3},
    {mtgfxns.israrity('r'), 1},
    {mtgfxns.israrity('m'), 0},
    {mtgfxns.island, 0}
  }
}

${draft_data}

for mtgsetcode, mtgsettable in pairs(mtgsets) do
  local setcardcount = mtgsettable.draftrules.cardcount
  local setminreqs = mtgsettable.draftrules.minreqs

  if string.len(mtgsetcode) == 3 and setcardcount < 15 then
    for colorruleidx = 1, 5 do
      setminreqs[colorruleidx][2] = 1
    end
  end
end

-- draft data --

local mtgdraft = {}

mtgdraft.setcodes = {${set_code_1}, ${set_code_2}, ${set_code_3}}
mtgdraft.settables = {
  mtgsets[mtgdraft.setcodes[1]],
  mtgsets[mtgdraft.setcodes[2]],
  mtgsets[mtgdraft.setcodes[3]]
}

mtgdraft.setidxs = {}
for codeidx, code in ipairs(mtgdraft.setcodes) do
  if mtgdraft.setidxs[code] == nil then mtgdraft.setidxs[code] = codeidx end
end

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
  -- scale land by rarity.
  return string.match(string.lower(card.type), '%f[%a]land%f[%A]')
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
    {iscolor('black'), 2},
    {island, 1}
  },
  maxreqs = {
    {israrity('c'), 11},
    {israrity('u'), 3},
    {israrity('r'), function(r) return r <= 7/8 and 1 or 0 end},
    {israrity('m'), function(r) return r > 7/8 and 1 or 0 end},
    {island, 1}
  }
}

-- NOTE(JRC): This is where the script automatically populates the output
-- file with all of the set data.
${draft_data}

--[[ tabletop functions ]]--

function onload()
  self.createButton({
    click_function = 'spawnextras',
    function_owner = self,
    label = 'Spawn Extras',
    position = {0.0, 0.0, 0.0},
    rotation = {180.0, 0.0, 0.0},
    width = 550,
    height = 200,
    font_size = 80
  })
end

function spawnextras()
  local deckids = {'54fd65', '54fd65', '54fd65'}
  local decksets = {mtgsets.${set_code_1}, mtgsets.${set_code_2}, mtgsets.${set_code_3}}

  local deckobjs = {}
  for _, deckid in ipairs(deckids) do table.insert(deckobjs, getObjectFromGUID(deckid)) end

  -- TODO(JRC): Automatically determine the size of the deck and adjust
  -- the location of the drafting area accordingly.
  local spawnbasepos = self.getPosition()
  local deckdims, bagdims = {w=2.5, h=0.25, d=3.5}, {w=2.5, h=1.0, d=2.5}
  local extrapercol = 3

  local deckcardobjlists = {}
  for deckidx, deckobj in ipairs(deckobjs) do
    local deckpos = deckobj.getPosition()
    local copypos = {x=deckpos.x, y=1, z=deckpos.z+deckdims.d}
    local deckcopy = deckobj.clone({copypos.x, copypos.y, copypos.z})

    local deckextras = {}
    for cardidx = 1, deckcopy.getQuantity() do
      local cardobj = deckcopy.takeObject({
        position={copypos.x, copypos.y+0.25*cardidx, copypos.z+deckdims.d},
        top=true
      })
      cardobj.lock()
      table.insert(deckextras, cardobj)
    end
    table.insert(deckcardobjlists, deckextras)
  end

  local landbasepos = {x=spawnbasepos.x-deckdims.w, y=1, z=spawnbasepos.z-deckdims.d}
  local landcount = 0
  for landidx, landextra in ipairs(decksets[1].extras) do
    if landextra.rarity == 'l' then
      landcount = landcount + 1
      local landrow = math.floor((landcount - 1) / extrapercol)
      local landcol = (landcount - 1) % extrapercol

      local landcard = deckcardobjlists[1][landidx]
      for landcopyidx = 1, 100 do
        local landcardobj = landcard.clone({
          position={
            landbasepos.x+landcol*deckdims.w,
            landbasepos.y+0.25*landcopyidx,
            landbasepos.z-landrow*deckdims.d
          },
          snap_to_grid=false
        })
        landcardobj.unlock()
      end
    end
  end

  local landrowcount = math.ceil(landcount / extrapercol)
  local extrabasepos = {
    x=spawnbasepos.x-deckdims.w,
    y=1,
    z=spawnbasepos.z-(landrowcount+1)*deckdims.d
  }
  local extracount = 0
  for deckidx, deckset in ipairs(decksets) do
    for extraidx, extra in ipairs(deckset.extras) do
      if extra.rarity ~= 'l' then
        extracount = extracount + 1
        local extrarow = math.floor((extracount - 1) / extrapercol)
        local extracol = (extracount - 1) % extrapercol

        local extracard = deckcardobjlists[deckidx][extraidx]
        local extrabagpos = {
          x=extrabasepos.x+extracol*bagdims.w,
          y=extrabasepos.y,
          z=extrabasepos.z-extrarow*bagdims.d
        }

        local extrabagobj = spawnObject({
          type='Infinite_Bag',
          position={extrabagpos.x, extrabagpos.y, extrabagpos.z},
          snap_to_grid=false
        })
        local extracardobj = extracard.clone({
          position={extrabagpos.x, extrabagpos.y+bagdims.h, extrabagpos.z},
          snap_to_grid=false
        })
        extrabagobj.lock()
        extracardobj.unlock()
        extracardobj.flip()
      end
    end
  end

  for _, deckcardobjlist in ipairs(deckcardobjlists) do
    for cardidx = #deckcardobjlist, 1, -1 do
      local cardobj = deckcardobjlist[cardidx]
      cardobj.destruct()
    end
  end
end

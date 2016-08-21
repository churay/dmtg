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
  local draftset2objs = {}
  for setidx, setcode in ipairs(mtgdraft.setcodes) do
    if draftset2objs[draftset] ~= nil then
      local setdeckobj = mtgdraft.extradeckobjs[setidx]
      draftset2objs[draftset] = mtgfxns.expanddeck(setdeckobj, 1)

      -- TODO(JRC): Try to elegantly merge this with the code for 'expanddeck'.
      for extraidx, extraobj in ipairs(draftset2objs[draftset]) do
        local extradata = mtgdraft.settables[setidx].extras[extraidx]
        extraobj.setName(extradata.name)
        extraobj.setDescription(extradata.rules)
      end
    end
  end

  -- TODO(JRC): Automatically determine the size of the deck and adjust
  -- the location of the drafting area accordingly.
  local spawnbasepos = self.getPosition()
  local bagdims = {w=2.5, h=1.0, d=2.5}
  local extrapercol = 3
  local landbasepos = {x=spawnbasepos.x-deckdims.w, y=1, z=spawnbasepos.z-deckdims.d}

  -- TODO(JRC): Basics are only taken from the first set as one set is generally
  -- all that's necessary, but this may need to be improved for sets with extra
  -- basics in different sets of the draft.
  local landcount = 0
  for landidx, landextra in ipairs(mtgdraft.settables[1].extras) do
    if landextra.rarity == 'l' then
      landcount = landcount + 1
      local landrow = math.floor((landcount - 1) / extrapercol)
      local landcol = (landcount - 1) % extrapercol

      local landcard = draftset2objs[mtgdraft.setcodes[1]][landidx]
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

  -- NOTE: Using the set codes from the 'draftset2objs' table eliminates
  -- redundant extras from being included.
  for setcode in pairs(draftset2objs) do
    local setidx = mtgfxns.getsetidx(setcode)
    local settable = mtgdraft.settables[setidx]
    for extraidx, extraextra in ipairs(settable.extras) do
      if extraextra.rarity ~= 'l' then
        extracount = extracount + 1
        local extrarow = math.floor((extracount - 1) / extrapercol)
        local extracol = (extracount - 1) % extrapercol

        local extracard = mtgdraft.extradeckobjs[setidx][extraidx]
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

  for _, setextras in pairs(draftset2objs) do
    mtgfxns.compressdeck(setextras)
  end
end

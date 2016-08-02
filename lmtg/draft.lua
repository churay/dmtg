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
  -- TODO(JRC): Figure out a better way to determine the deck's GUID so that
  -- it can be retrieved in this function automatically.
  local deckid = '07a2fc'
  local deckobj = getObjectFromGUID(deckid)
  local deckdims = {w=2.5, h=1/4, d=3.5}
  
  local deckpos = deckobj.getPosition()
  local deckcopypos = {x=deckpos.x-deckdims.w, y=1, z=deckpos.z}
  local draftdeckpos = {x=deckcopypos.x-deckdims.w, y=1, z=deckcopypos.z}
  local draftareapos = {x=draftdeckpos.x, y=1, z=draftdeckpos.z-deckdims.d}

  -- TODO(JRC): Automatically determine the size of the deck and adjust
  -- the location of the drafting area accordingly.
  local deckcopy = deckobj.clone({deckcopypos.x, deckcopypos.y, deckcopypos.z})
  local deckcards= {}
  for cardidx = 1, deckcopy.getQuantity() do
    local cardobj = deckcopy.takeObject({
      position={draftdeckpos.x, draftdeckpos.y+0.25*cardidx, draftdeckpos.z},
      callback='lockcard',
      callback_owner=self,
      params={},
      top=true
    })
    cardobj.lock()
    table.insert(deckcards, cardobj)
  end

  local boostercardcount, boostercolcount = 15, 3
  local boostercount = 3 -- 3 * #getSeatedPlayers()
  local cardsgenerated = {}
  for boosteridx = 1, boostercount do
    local boosterrow = math.floor((boosteridx-1) / boostercolcount)
    local boostercol = (boosteridx-1) % boostercolcount
    local boosterpos = {
      x=draftareapos.x+boostercol*deckdims.w,
      y=draftareapos.y,
      z=draftareapos.z-boosterrow*deckdims.d
    }

    for boostercardidx = 1, boostercardcount do
      -- TODO(JRC): Modify this code so that the booster generation process
      -- follows MTG booster generation rules.
      local cardidx = math.random(#deckcards)
      if cardsgenerated[cardidx] == nil then cardsgenerated[cardidx] = 1
      else cardsgenerated[cardidx] = cardsgenerated[cardidx] + 1 end
      local cardobj = deckcards[cardidx]
      local cardclone = cardobj.clone({
        position={boosterpos.x, boosterpos.y+0.25*boostercardidx, boosterpos.z},
        snap_to_grid=false
      })
      cardclone.unlock()
    end
  end
end

function lockcard(cardobj, params)
  cardobj.lock()
end

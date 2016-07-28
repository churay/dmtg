local mtgset = require('magic-cns.lua')

-- generate 10 commons, 3 uncommons, 1 rare (1/8 mythic rare)
-- generate all unique cards
-- place in at least one card of each color
-- place at least one land card in each (or 'draft-matters' if conspiracy)

-- random sort all, pop off and satisfy constraints ; need to not add if
-- there are x remaining limiting factors

function postostr(pos)
  return '(' .. pos[1] .. ', ' .. pos[2] .. ', ' .. pos[3] .. ')'
end

function draftcards()
  print('drafting cards...')
  local deckid = '61e522'
  local deckobj = getObjectFromGUID(deckid)

  deckobj.takeObject()
  deckobj.takeObject({index=10})

  --local deckcards = deckobj.getObjects()
  --print(deckobj.getQuantity())

  -- NOTE(JRC): The deck cards all have GUIDs, but these objects don't
  -- officially exist in TTS until they're removed from the deck.
  --[[
  local firstcard = getObjectFromGUID('238ccc') -- getObjectFromGUID(deckcards[1].guid)
  local firstcardpos = firstcard.getPosition()
  local newcardpos = {firstcardpos.x+1.0, firstcardpos.y, firstcardpos.z+1.0} 
  copy({firstcard})
  local newobjs = paste({position=newcardpos, snap_to_grid=true})

  for k, v in ipairs(getAllObjects()) do
    print('  ' .. v.guid)
  end
  ]]--
end

function onload()
  self.createButton({
    click_function='draftcards',
    function_owner= self,
    label='Draft Cards',
    position = {0.0, 0.5, 0.0},
    rotation = {0.0, 0.0, 0.0},
    width=450,
    height=200,
    font_size=80
  })
end

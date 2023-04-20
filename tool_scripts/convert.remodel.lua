-- Constants
local ARGS = {...}
local FILE_PATH = ARGS[1]
local OUT_PATH = ARGS[2]
local IS_MODEL = ARGS[3] == "true"

if IS_MODEL then
	local instList = remodel.readModelAsset(FILE_PATH)
	assert(#instList == 1, "can't be run on multi-root files: "..FILE_PATH)
	remodel.writeModelFile(OUT_PATH, instList[1])
else
	local place = remodel.readPlaceFile(FILE_PATH)
	remodel.writePlaceFile(OUT_PATH, place)
end

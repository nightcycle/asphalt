local ARGS = {...}
local SOUND_FILE_PATH = ARGS[1]
local model = fs.read(SOUND_FILE_PATH)

function setChildrenSoundGroups(inst)
	if inst.ClassName == "SoundGroup" then
		for i, child in ipairs(inst:GetChildren()) do
			if child.ClassName == "Sound" then
				child.SoundGroup = inst
			else
				child = setChildrenSoundGroups(child)
			end
		end
	end
	return inst
end

local firstModel = model:GetChildren()[1]
assert(#model:GetChildren() == 1, "only works on model files with a single instance. "..tostring(SOUND_FILE_PATH).." has "..tostring(#model:GetChildren()))
setChildrenSoundGroups(firstModel)

fs.write(SOUND_FILE_PATH, firstModel)
